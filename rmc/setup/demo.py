"""One month of realistic RMC plant operations.

Everything is generated through the app's own documents, so the demo exercises
the same code path a real plant does: material inwards raise purchase receipts,
batch production raises manufacture stock entries, delivery challans raise
sales invoices, and the orders' delivered/pending figures fall out of that.

    bench --site rmc.local execute rmc.setup.demo.build

Deterministic (seeded), and idempotent at the day level — a day that already
has batches is skipped, so it can be re-run to top up.
"""

import random
import frappe
from frappe.utils import add_days, getdate, get_datetime, flt

SEED = 20260805
DAYS = 31                      # rolling month ending today
WORKING_SHIFTS = ["Shift A", "Shift B"]

CUSTOMERS = [
	("Sri Venkateswara Constructions Pvt Ltd", "Vizag"),
	("Coastal Infra Projects Ltd", "Vizag"),
	("Gayatri Builders and Developers", "Vizag"),
	("NCC Infrastructure Ltd", "Anakapalle"),
	("Ramky Housing Pvt Ltd", "Vizag"),
	("Sagar Cements Township Project", "Bheemili"),
	("APSRTC Depot Works", "Gajuwaka"),
	("Vizag Port Trust Works", "Vizag Port"),
]

SITES = [
	# (site name, customer index, distance km, grades commonly poured)
	("Sagar Skyline Tower - Block A", 0, 12.5, ["M25", "M30"]),
	("Sagar Skyline Tower - Block B", 0, 12.5, ["M25", "M35"]),
	("Coastal IT Park Phase 2", 1, 18.0, ["M30", "M40"]),
	("Coastal Marine Drive Widening", 1, 24.0, ["M20", "M30"]),
	("Gayatri Residency Enclave", 2, 8.5, ["M20", "M25"]),
	("NCC Flyover Package 3", 3, 31.0, ["M35", "M40", "M50"]),
	("Ramky Green Homes Tower 4", 4, 15.5, ["M25", "M30"]),
	("Sagar Township Roads", 5, 27.0, ["M10", "M15", "M20"]),
	("APSRTC Depot Yard Concreting", 6, 9.0, ["M15", "M25"]),
	("Port Berth 8 Hard Standing", 7, 21.0, ["M40", "M50"]),
]

MIXERS = [
	("AP31 TA 4501", "Transit Mixer", 6.0),
	("AP31 TA 4502", "Transit Mixer", 6.0),
	("AP31 TA 4503", "Transit Mixer", 6.0),
	("AP31 TB 7788", "Transit Mixer", 7.0),
	("AP31 TB 7789", "Transit Mixer", 7.0),
	("AP31 TC 1120", "Transit Mixer", 8.0),
	("AP31 TC 1121", "Transit Mixer", 8.0),
	("AP39 TD 3344", "Transit Mixer", 6.0),
	("AP31 CP 9001", "Concrete Pump", 0.0),
	("AP31 CP 9002", "Concrete Pump", 0.0),
]

DRIVERS = [
	"Ramesh Naidu", "Suresh Kumar", "Appa Rao", "Md. Ismail", "Satyanarayana",
	"Venkat Rao", "Prasad Babu", "Nagaraju", "Srinivas Reddy", "Bhaskar Rao",
]

SUPPLIERS = [
	("Ultratech Cement Ltd", ["RM-CEM-OPC53", "RM-CEM-PPC"]),
	("Sagar Cements Ltd", ["RM-CEM-OPC53"]),
	("Godavari Sand Suppliers", ["RM-SAND", "RM-MSAND"]),
	("Vizag Aggregates and Metals", ["RM-AGG20", "RM-AGG10"]),
	("NTPC Fly Ash Depot", ["RM-FLYASH"]),
	("Fosroc Chemicals India", ["RM-ADMIX"]),
	("JSW Slag Products", ["RM-GGBS"]),
	# Batching water is tankered in and costed like any other ingredient, so it
	# has a supplier too — otherwise the water tank can never be replenished.
	("Vizag Municipal Water Tankers", ["RM-WATER"]),
]

OPERATORS = ["K. Srinivas", "B. Ravi Kumar", "M. Anil", "T. Prakash"]
QC_ENGINEERS = ["Er. Lakshmi Prasanna", "Er. Vamsi Krishna", "Er. Sneha Rani"]

BREAKDOWN_REASONS = [
	("Mixer", "Mixer blade wear — discharge slow", "Blades re-tipped and gap reset", "Medium"),
	("Conveyor", "Aggregate belt slipping under load", "Belt re-tensioned, idler replaced", "Medium"),
	("Weighing System", "Cement load cell drift on weigh hopper", "Load cell re-calibrated", "High"),
	("Air Compressor", "Air pressure low — silo butterfly valve sluggish", "Compressor filter and unloader valve replaced", "Medium"),
	("Cement Silo", "Silo aeration pad choked, cement bridging", "Pads cleaned, aeration line blown", "High"),
	("DG Set", "DG tripped on high coolant temperature", "Radiator cleaned, coolant topped up", "Low"),
	("Water System", "Water pump seal leak at batching point", "Mechanical seal replaced", "Low"),
	("Transit Mixer", "Drum drive hydraulic hose burst", "Hose replaced, hydraulic oil topped", "High"),
]

MAINT = [
	("Batching Plant — general greasing", "Weekly"),
	("Mixer gearbox oil check", "Monthly"),
	("Load cell calibration (cement / aggregate / water)", "Quarterly"),
	("Cement silo filter cleaning", "Monthly"),
	("DG set servicing", "Quarterly"),
	("Transit mixer drum inspection", "Monthly"),
	("Air compressor service", "Half Yearly"),
	("Weighbridge calibration", "Half Yearly"),
]


def _rng():
	return random.Random(SEED)


# ---------------------------------------------------------------- masters
def build_masters(rng):
	from rmc.setup.masters import PLANT_NAME

	for cust, city in CUSTOMERS:
		if not frappe.db.exists("Customer", cust):
			frappe.get_doc({
				"doctype": "Customer", "customer_name": cust,
				"customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name"),
				"territory": frappe.db.get_value("Territory", {"is_group": 0}, "name"),
				"customer_type": "Company",
			}).insert(ignore_permissions=True)

	for supp, _items in SUPPLIERS:
		if not frappe.db.exists("Supplier", supp):
			frappe.get_doc({
				"doctype": "Supplier", "supplier_name": supp,
				"supplier_group": frappe.db.get_value("Supplier Group", {"is_group": 0}, "name"),
			}).insert(ignore_permissions=True)

	for name in DRIVERS:
		if not frappe.db.exists("Driver", {"full_name": name}):
			frappe.get_doc({
				"doctype": "Driver", "full_name": name, "status": "Active",
				"license_number": "AP31%s" % rng.randint(20000000, 29999999),
				"cell_number": "9%s" % rng.randint(100000000, 999999999),
			}).insert(ignore_permissions=True)
	driver_names = frappe.get_all("Driver", pluck="name")

	for i, (veh, vtype, cap) in enumerate(MIXERS):
		if frappe.db.exists("Transit Mixer", veh):
			continue
		frappe.get_doc({
			"doctype": "Transit Mixer", "vehicle_no": veh, "vehicle_type": vtype,
			"capacity_m3": cap, "plant": PLANT_NAME,
			"make": rng.choice(["Ashok Leyland 2518", "Tata Signa 2823", "BharatBenz 2828"]),
			"ownership": "Own" if i < 7 else "Hired",
			"default_driver": driver_names[i % len(driver_names)] if driver_names else None,
			"status": "Available",
			"fitness_valid_upto": "2027-03-31", "insurance_valid_upto": "2026-12-31",
		}).insert(ignore_permissions=True)

	for site, ci, dist, _grades in SITES:
		if frappe.db.exists("Construction Site", {"site_name": site}):
			continue
		cust = CUSTOMERS[ci][0]
		frappe.get_doc({
			"doctype": "Construction Site", "site_name": site, "customer": cust,
			"site_address": "%s, %s, Andhra Pradesh" % (site, CUSTOMERS[ci][1]),
			"city": CUSTOMERS[ci][1], "distance_km": dist,
			"contact_person": rng.choice(["Site Engineer", "Project Manager", "Site Incharge"]),
			"contact_no": "9%s" % rng.randint(100000000, 999999999),
			"pump_access": 1, "is_active": 1,
		}).insert(ignore_permissions=True)

	today = getdate()
	for i, (equip, freq) in enumerate(MAINT):
		if frappe.db.exists("RMC Maintenance Task", {"equipment": equip}):
			continue
		nxt = add_days(today, rng.randint(-6, 20))
		frappe.get_doc({
			"doctype": "RMC Maintenance Task", "equipment": equip, "plant": PLANT_NAME,
			"frequency": freq, "last_done_on": add_days(nxt, -30),
			"next_due_on": nxt, "responsible": rng.choice(OPERATORS),
			"status": "Overdue" if nxt < today else ("Due" if nxt == today else "Scheduled"),
			"checklist": "As per OEM manual — %s check." % freq.lower(),
		}).insert(ignore_permissions=True)

	frappe.db.commit()
	print("  + masters: %d customers, %d sites, %d mixers, %d drivers, %d suppliers"
	      % (len(CUSTOMERS), len(SITES), len(MIXERS), len(DRIVERS), len(SUPPLIERS)))


# ---------------------------------------------------------------- opening stock
def opening_stock(rng, start_date):
	"""Fill every silo before day one, else the first batch has nothing to consume."""
	from rmc.setup.masters import PLANT_NAME

	plant = frappe.get_doc("RMC Plant", PLANT_NAME)
	if frappe.db.exists("Stock Entry", {"stock_entry_type": "Material Receipt",
	                                    "posting_date": start_date, "docstatus": 1}):
		return
	se = frappe.new_doc("Stock Entry")
	se.stock_entry_type = "Material Receipt"
	se.purpose = "Material Receipt"
	se.company = plant.company
	se.posting_date = start_date
	se.set_posting_time = 1
	se.posting_time = "06:00:00"
	for silo in frappe.get_all("Silo", filters={"is_active": 1},
	                           fields=["item_code", "warehouse", "capacity_mt"]):
		rate = flt(frappe.db.get_value("Item", silo.item_code, "valuation_rate")) or 1
		qty = flt(silo.capacity_mt) * 1000 * 0.90          # start each silo ~90% full
		se.append("items", {"item_code": silo.item_code, "qty": qty,
		                    "t_warehouse": silo.warehouse, "basic_rate": rate,
		                    "allow_zero_valuation_rate": 1})
	se.flags.ignore_permissions = True
	se.insert()
	se.submit()
	frappe.db.commit()
	print("  + opening stock in %d silos" % len(se.items))


# ---------------------------------------------------------------- inwards
# Truck / tanker sizes per material type, in MT (or kL for the liquids).
LOAD_SIZE = {
	"Cement": (24, 30),
	"Fly Ash": (20, 26),
	"GGBS": (20, 26),
	"Sand": (26, 35),
	"Aggregate": (26, 35),
	"Admixture": (6, 10),
	"Water": (20, 28),
}

# Which supplier sells what — a truck must come from a supplier who stocks it.
SUPPLIER_OF = {}
for _s, _items in SUPPLIERS:
	for _i in _items:
		SUPPLIER_OF.setdefault(_i, []).append(_s)


def top_up_before_batch(rng, day, plant, mix_design, qty_m3):
	"""Guarantee the batch about to be poured has its materials.

	Replenishment runs once each morning; a heavy day can still drain a fast
	moving tank (water, admixture) before the last load. Rather than let the
	stock ledger throw mid-month, call in the extra tanker the storekeeper
	would have called in.
	"""
	design = frappe.get_doc("Mix Design", mix_design)
	for d in design.items:
		need = flt(d.qty_per_m3) * flt(qty_m3) * 1.05
		silo = frappe.db.get_value("Silo", {"item_code": d.item_code, "is_active": 1},
		                           ["name", "warehouse", "capacity_mt", "material_type"],
		                           as_dict=True)
		if not silo:
			continue
		on_hand = flt(frappe.db.get_value("Bin", {"item_code": d.item_code,
		                                          "warehouse": silo.warehouse}, "actual_qty"))
		if on_hand >= need:
			continue
		suppliers = SUPPLIER_OF.get(d.item_code)
		if not suppliers:
			continue
		lo, hi = LOAD_SIZE.get(silo.material_type, (20, 30))
		shortfall_mt = max((need - on_hand) / 1000.0, lo * 0.5)
		net = round(min(max(shortfall_mt * 1.5, lo), hi), 3)
		tare = round(rng.uniform(12.5, 15.5), 3)
		rate = flt(frappe.db.get_value("Item", d.item_code, "valuation_rate")) * 1000
		doc = frappe.get_doc({
			"doctype": "Material Inward", "inward_date": day, "plant": plant,
			"inward_time": "04:%02d:00" % rng.randint(0, 59),
			"supplier": rng.choice(suppliers),
			"supplier_dc_no": "DC%s" % rng.randint(10000, 99999),
			"item_code": d.item_code, "silo": silo.name,
			"vehicle_no": "AP%s %s %s" % (rng.randint(16, 39),
			                              rng.choice(["TX", "TY", "TZ", "UA"]),
			                              rng.randint(1000, 9999)),
			"gross_weight": round(tare + net, 3), "tare_weight": tare,
			"net_weight": net, "rate": round(rate * rng.uniform(0.97, 1.03), 2),
			"quality_ok": 1,
			"test_report": "QC/%s/%s" % (getdate(day).strftime("%m%d"), rng.randint(100, 999)),
		})
		doc.flags.ignore_permissions = True
		doc.insert()
		doc.submit()


def replenish_silos(rng, day, plant):
	"""Order material the way a plant storekeeper does: look at each silo, and
	if it has fallen below ~45% of capacity, call in trucks until it is back to
	~85%. This keeps a month of production supplied without ever running dry —
	random inwards do not, because consumption far outruns them.
	"""
	trucks = 0
	for silo in frappe.get_all("Silo", filters={"is_active": 1},
	                           fields=["name", "item_code", "warehouse", "capacity_mt",
	                                   "material_type"]):
		suppliers = SUPPLIER_OF.get(silo.item_code)
		if not suppliers:
			continue
		capacity = flt(silo.capacity_mt)
		on_hand = flt(frappe.db.get_value("Bin", {"item_code": silo.item_code,
		                                          "warehouse": silo.warehouse},
		                                  "actual_qty")) / 1000.0
		if on_hand > capacity * 0.60:
			continue
		target = capacity * 0.95
		lo, hi = LOAD_SIZE.get(silo.material_type, (20, 30))
		for _ in range(8):                       # at most 8 trucks per silo per day
			if on_hand >= target:
				break
			net = round(min(rng.uniform(lo, hi), max(target - on_hand, lo * 0.5)), 3)
			tare = round(rng.uniform(12.5, 15.5), 3)
			rate = flt(frappe.db.get_value("Item", silo.item_code, "valuation_rate")) * 1000
			doc = frappe.get_doc({
				"doctype": "Material Inward", "inward_date": day, "plant": plant,
				"inward_time": "0%d:%02d:00" % (rng.randint(4, 5), rng.randint(0, 59)),
				"supplier": rng.choice(suppliers),
				"supplier_dc_no": "DC%s" % rng.randint(10000, 99999),
				"item_code": silo.item_code, "silo": silo.name,
				"vehicle_no": "AP%s %s %s" % (rng.randint(16, 39),
				                              rng.choice(["TX", "TY", "TZ", "UA"]),
				                              rng.randint(1000, 9999)),
				"gross_weight": round(tare + net, 3), "tare_weight": tare,
				"net_weight": net, "rate": round(rate * rng.uniform(0.97, 1.03), 2),
				"quality_ok": 1,
				"test_report": "QC/%s/%s" % (getdate(day).strftime("%m%d"),
				                             rng.randint(100, 999)),
			})
			doc.flags.ignore_permissions = True
			doc.insert()
			doc.submit()
			on_hand += net
			trucks += 1
	return trucks


# ---------------------------------------------------------------- daily ops
def build_days(rng, start_date, days):
	from rmc.setup.masters import PLANT_NAME

	plant = PLANT_NAME
	mixers = [m[0] for m in MIXERS if m[1] == "Transit Mixer"]
	mixer_cap = {m[0]: m[2] for m in MIXERS}
	drivers = frappe.get_all("Driver", pluck="name")
	sites = frappe.get_all("Construction Site", fields=["name", "site_name", "customer",
	                                                   "distance_km"])
	site_grades = {s[0]: s[3] for s in SITES}
	site_by_label = {s.site_name: s for s in sites}

	made = {"orders": 0, "batches": 0, "challans": 0, "inwards": 0,
	        "cubes": 0, "status": 0, "breakdowns": 0, "power": 0}

	open_orders = []          # [(order_name, site, grade, rate, pending_m3)]

	for d in range(days):
		day = add_days(start_date, d)
		weekday = getdate(day).weekday()
		if frappe.db.exists("Batch Production", {"production_date": day, "docstatus": 1}):
			continue

		# ---- material inwards: replenish whatever the plant actually burnt ----
		if weekday != 6:
			made["inwards"] += replenish_silos(rng, day, plant)

		# ---- new customer orders ----
		# Sized so the order book roughly matches what the plant can pour in a
		# day (~80 m³); more than that and the backlog grows without end.
		for _ in range(rng.randint(1, 2)):
			label, ci, dist, grades = rng.choice(SITES)
			site = site_by_label.get(label)
			if not site:
				continue
			grade = rng.choice(grades)
			qty = float(rng.choice([24, 30, 36, 45, 54, 60, 75, 90, 120]))
			rate = flt(frappe.db.get_value("Concrete Grade", grade, "default_rate"))
			rate = round(rate * rng.uniform(0.97, 1.04), 2)
			req_from = add_days(day, rng.randint(0, 2))
			order = frappe.get_doc({
				"doctype": "Concrete Order", "customer": site.customer,
				"construction_site": site.name, "order_date": day, "grade": grade,
				"order_qty_m3": qty, "rate": rate,
				"required_from": req_from, "required_to": add_days(req_from, rng.randint(0, 3)),
				"pump_required": 1 if qty >= 90 else 0,
				"site_engineer": rng.choice(["Er. Ravi", "Er. Kiran", "Er. Naveen", "Er. Suresh"]),
				"contact_no": "9%s" % rng.randint(100000000, 999999999),
				"schedule": [{"schedule_date": req_from, "time_slot": "06:00 - 14:00",
				              "qty_m3": qty}],
				"remarks": "Pour for %s." % label,
			})
			order.flags.ignore_permissions = True
			order.insert()
			order.submit()
			made["orders"] += 1
			open_orders.append([order.name, site.name, grade, rate, qty, site.distance_km])

		# ---- production + dispatch against the open orders ----
		if weekday != 6:
			loads_today = rng.randint(8, 16)
			hour = 6
			for load in range(loads_today):
				open_orders = [o for o in open_orders if o[4] > 0.5]
				if not open_orders:
					break
				o = rng.choice(open_orders)
				order_name, site_name, grade, rate, pending, dist = o
				mixer = rng.choice(mixers)
				cap = mixer_cap.get(mixer, 6.0)
				qty = min(cap, round(pending, 2))
				if qty <= 0:
					continue

				shift = WORKING_SHIFTS[0] if hour < 14 else WORKING_SHIFTS[1]
				mix = frappe.db.get_value("Mix Design", {"grade": grade, "is_active": 1}, "name")
				top_up_before_batch(rng, day, plant, mix, qty)
				start = get_datetime("%s %02d:%02d:00" % (day, hour % 24, rng.randint(0, 45)))
				end = get_datetime(start).replace(minute=min(59, get_datetime(start).minute + 12))

				batch = frappe.get_doc({
					"doctype": "Batch Production", "production_date": day, "plant": plant,
					"shift": shift, "grade": grade, "mix_design": mix,
					"concrete_order": order_name, "qty_m3": qty,
					"no_of_batches": max(1, int(qty // 2)),
					"start_time": start, "end_time": end,
					"operator": rng.choice(OPERATORS),
					"remarks": "Batched for %s" % site_name,
				})
				batch.flags.ignore_permissions = True
				batch.insert()
				# real plants never hit the recipe exactly — dose within ±2%
				for row in batch.materials:
					row.actual_qty = round(flt(row.target_qty) * rng.uniform(0.985, 1.015), 3)
				batch.save()
				batch.submit()
				made["batches"] += 1

				travel = int(dist * rng.uniform(2.0, 3.2)) + 5
				dispatch = get_datetime(end)
				arrival = frappe.utils.add_to_date(dispatch, minutes=travel)
				unload_end = frappe.utils.add_to_date(arrival, minutes=rng.randint(20, 45))
				back = frappe.utils.add_to_date(unload_end, minutes=travel + rng.randint(0, 15))

				challan = frappe.get_doc({
					"doctype": "Delivery Challan", "concrete_order": order_name,
					"challan_date": day, "grade": grade, "qty_m3": qty, "rate": rate,
					"transit_mixer": mixer,
					"driver": rng.choice(drivers) if drivers else None,
					"batch_production": batch.name,
					"dispatch_time": dispatch, "site_arrival_time": arrival,
					"unloading_end_time": unload_end, "return_time": back,
					"slump_mm": rng.choice([90, 100, 110, 120, 130, 140]),
					"temperature_c": round(rng.uniform(28, 36), 1),
					"cubes_taken": 1 if rng.random() < 0.25 else 0,
					"status": "Returned",
					"received_by": rng.choice(["Site Engineer", "Store Incharge", "Foreman"]),
				})
				challan.flags.ignore_permissions = True
				challan.insert()
				challan.submit()
				made["challans"] += 1

				o[4] = round(pending - qty, 2)

				# ---- cube tests on ~25% of loads ----
				if challan.cubes_taken:
					characteristic = flt(frappe.db.get_value("Concrete Grade", grade,
					                                         "strength_mpa"))
					for age in (7, 28):
						# 28-day tests only exist if that date has already passed
						test_date = add_days(getdate(day), age)
						if test_date > getdate():
							continue
						factor = 0.65 if age == 7 else 1.0
						# ~94% of tests comfortably pass; the rest fall just short
						achieved = characteristic * factor * (
							rng.uniform(1.02, 1.18) if rng.random() > 0.06
							else rng.uniform(0.86, 0.98))
						ct = frappe.get_doc({
							"doctype": "Cube Test", "batch_production": batch.name,
							"grade": grade, "casting_date": day, "age_days": str(age),
							"testing_date": test_date, "no_of_cubes": 3,
							"delivery_challan": challan.name,
							"avg_strength_mpa": round(achieved, 1),
							"tested_by": rng.choice(QC_ENGINEERS),
							"remarks": "Cast from %s" % batch.name,
						})
						ct.flags.ignore_permissions = True
						ct.insert()
						ct.submit()
						made["cubes"] += 1

				hour += 1
				if hour > 20:
					break

		# ---- plant status log for the day ----
		made["status"] += _status_log(rng, day, plant, weekday)

		# ---- occasional breakdown (~18% of days) ----
		if weekday != 6 and rng.random() < 0.18:
			equip, reason, action, sev = rng.choice(BREAKDOWN_REASONS)
			start = get_datetime("%s %02d:%02d:00" % (day, rng.randint(7, 17), rng.randint(0, 59)))
			hours = rng.uniform(0.5, 4.0)
			bd = frappe.get_doc({
				"doctype": "Breakdown Log", "plant": plant, "equipment": equip,
				"reported_on": start,
				"resolved_on": frappe.utils.add_to_date(start, minutes=int(hours * 60)),
				"status": "Closed", "severity": sev, "reason": reason,
				"action_taken": action, "attended_by": rng.choice(OPERATORS),
				"spare_cost": round(rng.uniform(1500, 28000), 0),
			})
			if equip == "Transit Mixer":
				bd.transit_mixer = rng.choice(mixers)
			bd.flags.ignore_permissions = True
			bd.insert()
			made["breakdowns"] += 1

		# ---- power log ----
		if not frappe.db.exists("Power Log", {"log_date": day, "plant": plant}):
			eb_h = 0 if weekday == 6 else round(rng.uniform(8, 13), 1)
			dg_h = round(rng.uniform(0, 2.5), 1) if rng.random() < 0.5 else 0
			diesel = round(dg_h * rng.uniform(11, 14), 1)
			frappe.get_doc({
				"doctype": "Power Log", "log_date": day, "plant": plant,
				"eb_units": round(eb_h * rng.uniform(90, 130), 1), "eb_hours": eb_h,
				"dg_units": round(dg_h * rng.uniform(75, 110), 1), "dg_hours": dg_h,
				"diesel_litres": diesel, "diesel_cost": round(diesel * 92.5, 2),
				"remarks": "EB supply normal." if dg_h == 0 else "DG run during EB interruption.",
			}).insert(ignore_permissions=True)
			made["power"] += 1

		frappe.db.commit()

	print("  + demo operations: %s" % made)
	return made


def _status_log(rng, day, plant, weekday):
	"""Running / idle / breakdown blocks that add up to the working window."""
	if frappe.db.exists("Plant Status Log", {"log_date": day, "plant": plant}):
		return 0
	blocks = 0
	if weekday == 6:                      # Sunday: maintenance shutdown
		spans = [("Stopped", 6, 18, "Sunday — weekly maintenance shutdown")]
	else:
		run1 = rng.uniform(5.5, 7.5)
		idle = rng.uniform(0.5, 1.5)
		run2 = rng.uniform(3.5, 5.5)
		spans = [
			("Running", 6, 6 + run1, "Normal batching"),
			("Idle", 6 + run1, 6 + run1 + idle, "Awaiting trucks / order gap"),
			("Running", 6 + run1 + idle, 6 + run1 + idle + run2, "Second shift batching"),
		]
		if rng.random() < 0.2:
			spans.append(("Breakdown", 6 + run1 + idle + run2,
			              6 + run1 + idle + run2 + rng.uniform(0.4, 1.6),
			              "Unplanned stoppage — see breakdown log"))
	for status, frm, to, reason in spans:
		frappe.get_doc({
			"doctype": "Plant Status Log", "log_date": day, "plant": plant,
			"shift": "Shift A" if frm < 14 else "Shift B", "status": status,
			"from_time": _dt(day, frm), "to_time": _dt(day, to),
			"power_source": "EB", "eb_voltage": round(rng.uniform(405, 425), 1),
			"dg_load_pct": 0, "reason": reason,
		}).insert(ignore_permissions=True)
		blocks += 1
	return blocks


def _dt(day, hours_float):
	h = int(hours_float) % 24
	m = int(round((hours_float - int(hours_float)) * 60)) % 60
	return get_datetime("%s %02d:%02d:00" % (day, h, m))


def reset():
	"""Wipe every transaction (keeping masters) so the month can be rebuilt.

	Demo-site only: it clears the ledgers directly rather than cancelling
	thousands of documents one by one.
	"""
	tables = [
		"Cube Test", "Delivery Challan", "Batch Material", "Batch Production",
		"Order Schedule", "Concrete Order", "Material Inward",
		"Plant Status Log", "Breakdown Log", "Power Log",
		"Sales Invoice Item", "Sales Taxes and Charges", "Payment Schedule",
		"Sales Invoice", "Purchase Receipt Item", "Purchase Receipt",
		"Stock Entry Detail", "Stock Entry",
		"GL Entry", "Stock Ledger Entry", "Bin", "Repost Item Valuation",
		"Serial and Batch Bundle", "Serial and Batch Entry",
	]
	for t in tables:
		try:
			frappe.db.sql("DELETE FROM `tab%s`" % t)
		except Exception:
			pass
	frappe.db.commit()
	print("  - reset: transactions cleared, masters kept")


def build():
	rng = _rng()
	start = add_days(getdate(), -(DAYS - 1))
	print("Building RMC demo data %s -> %s" % (start, getdate()))
	build_masters(rng)
	opening_stock(rng, start)
	build_days(rng, start, DAYS)
	from rmc import tasks
	tasks.refresh_order_status()
	tasks.flag_due_maintenance()
	frappe.db.commit()
	print("Demo data complete.")

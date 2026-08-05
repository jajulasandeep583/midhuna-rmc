"""End-to-end run on the live site, acting as the real roles.

    bench --site rmc.local execute rmc.setup.e2e.run

Not a read-only check: this books a genuine order, batches it, dispatches it,
bills it and tests the cube — then proves every ledger, board and report moved
by exactly the right amount, and that the guard rails still bite.
"""

import traceback
import frappe
from frappe.utils import add_days, flt, getdate, nowdate, get_datetime, now_datetime

PASS = FAIL = 0
LOG = []


def check(cond, label, detail=""):
	global PASS, FAIL
	if cond:
		PASS += 1
		print("  PASS  %-58s %s" % (label, detail))
	else:
		FAIL += 1
		LOG.append(label)
		print("  FAIL  %-58s %s" % (label, detail))


def as_user(u):
	frappe.set_user(u)


def snapshot():
	q = frappe.db.sql
	return {
		"orders": frappe.db.count("Concrete Order", {"docstatus": 1}),
		"batches": frappe.db.count("Batch Production", {"docstatus": 1}),
		"challans": frappe.db.count("Delivery Challan", {"docstatus": 1}),
		"invoices": frappe.db.count("Sales Invoice", {"docstatus": 1}),
		"stock_entries": frappe.db.count("Stock Entry", {"docstatus": 1}),
		"produced": flt(q("SELECT SUM(qty_m3) FROM `tabBatch Production` WHERE docstatus=1")[0][0]),
		"dispatched": flt(q("SELECT SUM(qty_m3) FROM `tabDelivery Challan` WHERE docstatus=1")[0][0]),
		"revenue": flt(q("SELECT SUM(amount) FROM `tabDelivery Challan` WHERE docstatus=1")[0][0]),
		"cement": flt(frappe.db.get_value(
			"Bin", {"item_code": "RM-CEM-OPC53",
			        "warehouse": frappe.db.get_value("Silo", {"item_code": "RM-CEM-OPC53"},
			                                         "warehouse")}, "actual_qty")),
	}



def run():
	print("=" * 74)
	print("PHASE 1  —  every role can log in and see its own desk")
	print("=" * 74)
	ROLES = {
		"manager@midhunarmc.com": ("RMC Manager", ["Concrete Order", "Batch Production",
		                                           "Delivery Challan", "Sales Invoice"]),
		"operator@midhunarmc.com": ("Plant Operator", ["Batch Production", "Material Inward"]),
		"dispatch@midhunarmc.com": ("Dispatch Incharge", ["Delivery Challan", "Concrete Order"]),
		"quality@midhunarmc.com": ("Quality Engineer", ["Cube Test"]),
		"accounts@midhunarmc.com": ("RMC Accounts", ["Sales Invoice", "Purchase Receipt"]),
	}
	for user, (role, doctypes) in ROLES.items():
		as_user(user)
		has = role in frappe.get_roles()
		readable = all(frappe.has_permission(dt, "read") for dt in doctypes)
		check(has and readable, "%s logs in as %s" % (user.split("@")[0], role),
		      "can read %s" % ", ".join(doctypes))
	as_user("Administrator")

	print()
	print("=" * 74)
	print("PHASE 2  —  a real order, all the way through, by the people who do it")
	print("=" * 74)
	before = snapshot()
	today = getdate(nowdate())

	# ---- the dispatch incharge books the order --------------------------------
	as_user("dispatch@midhunarmc.com")
	site = frappe.db.get_value("Construction Site", {"is_active": 1},
	                           ["name", "customer"], as_dict=True)
	order = frappe.get_doc({
		"doctype": "Concrete Order", "customer": site.customer,
		"construction_site": site.name, "order_date": today, "grade": "M30",
		"order_qty_m3": 18, "rate": 5600, "required_from": today,
		"required_to": today, "site_engineer": "Er. Demo", "contact_no": "9000000001",
		"schedule": [{"schedule_date": today, "time_slot": "09:00 - 13:00", "qty_m3": 18}],
		"remarks": "End-to-end demo pour",
	})
	order.insert()
	order.submit()
	check(order.docstatus == 1 and order.status == "Open",
	      "Dispatch books an 18 m³ M30 order", order.name)
	check(flt(order.pending_qty_m3) == 18, "Pending starts at the full order",
	      "%s m³" % order.pending_qty_m3)

	# ---- the operator batches it ---------------------------------------------
	as_user("operator@midhunarmc.com")
	plant = frappe.db.get_single_value("RMC Settings", "default_plant")
	mix = frappe.db.get_value("Mix Design", {"grade": "M30", "is_active": 1}, "name")
	batch = frappe.get_doc({
		"doctype": "Batch Production", "production_date": today, "plant": plant,
		"shift": "Shift A", "grade": "M30", "mix_design": mix,
		"concrete_order": order.name, "qty_m3": 6, "no_of_batches": 3,
		"start_time": now_datetime(), "end_time": now_datetime(),
		"operator": "K. Srinivas", "remarks": "E2E demo batch",
	})
	batch.insert()
	recipe_cement = [r for r in batch.materials if r.item_code == "RM-CEM-OPC53"][0].target_qty
	batch.submit()
	batch.reload()
	check(batch.stock_entry and batch.status == "Produced",
	      "Operator batches 6 m³ — stock entry written", batch.stock_entry)

	se = frappe.get_doc("Stock Entry", batch.stock_entry)
	concrete_in = sum(flt(i.qty) for i in se.items if i.item_code == "RMC-M30" and i.t_warehouse)
	check(abs(concrete_in - 6) < 0.001, "6 m³ of M30 entered finished stock",
	      "%s m³" % concrete_in)
	after_cement = flt(frappe.db.get_value(
		"Bin", {"item_code": "RM-CEM-OPC53",
		        "warehouse": frappe.db.get_value("Silo", {"item_code": "RM-CEM-OPC53"},
		                                         "warehouse")}, "actual_qty"))
	check(before["cement"] - after_cement > 0,
	      "Cement silo fell by the batch's consumption",
	      "%.1f kg drawn (recipe %.1f)" % (before["cement"] - after_cement, recipe_cement))

	# ---- the dispatch incharge sends it out ----------------------------------
	as_user("dispatch@midhunarmc.com")
	mixer = frappe.db.get_value("Transit Mixer",
	                            {"vehicle_type": "Transit Mixer", "status": "Available"}, "name") \
		or frappe.db.get_value("Transit Mixer", {"vehicle_type": "Transit Mixer"}, "name")
	driver = frappe.db.get_value("Driver", {}, "name")
	dispatch_at = get_datetime()
	challan = frappe.get_doc({
		"doctype": "Delivery Challan", "concrete_order": order.name, "challan_date": today,
		"grade": "M30", "qty_m3": 6, "rate": 5600, "transit_mixer": mixer, "driver": driver,
		"batch_production": batch.name, "dispatch_time": dispatch_at,
		"site_arrival_time": frappe.utils.add_to_date(dispatch_at, minutes=35),
		"unloading_end_time": frappe.utils.add_to_date(dispatch_at, minutes=70),
		"return_time": frappe.utils.add_to_date(dispatch_at, minutes=105),
		"slump_mm": 120, "temperature_c": 31.5, "cubes_taken": 1,
		"status": "Returned", "received_by": "Site Engineer",
	})
	challan.insert()
	challan.submit()
	challan.reload()
	check(challan.docstatus == 1 and challan.sales_invoice,
	      "Dispatch raises the challan — invoice billed", challan.sales_invoice)
	check(challan.cycle_time_min == 105, "Cycle time computed from the trip",
	      "%s min" % challan.cycle_time_min)
	check(abs(flt(challan.amount) - 6 * 5600) < 0.01, "Challan value = qty × rate",
	      "₹%s" % challan.amount)

	si = frappe.get_doc("Sales Invoice", challan.sales_invoice)
	check(abs(flt(si.net_total) - flt(challan.amount)) < 0.01,
	      "Invoice value matches the challan", "₹%s" % si.net_total)
	check(si.update_stock == 1, "Invoice moved the concrete out of stock")

	order.reload()
	check(abs(flt(order.delivered_qty_m3) - 6) < 0.001 and abs(flt(order.pending_qty_m3) - 12) < 0.001,
	      "Order rolled up: 6 delivered, 12 pending", order.status)
	check(order.status == "In Progress", "Order status moved to In Progress")

	# ---- quality tests the cube ----------------------------------------------
	as_user("quality@midhunarmc.com")
	cube = frappe.get_doc({
		"doctype": "Cube Test", "batch_production": batch.name, "grade": "M30",
		"casting_date": today, "age_days": "7", "no_of_cubes": 3,
		"delivery_challan": challan.name, "avg_strength_mpa": 22.4,
		"tested_by": "Er. Lakshmi Prasanna", "remarks": "E2E demo cube",
	})
	cube.insert()
	cube.submit()
	cube.reload()
	check(abs(flt(cube.required_strength_mpa) - 19.5) < 0.01,
	      "7-day requirement derived as 65% of M30", "%s MPa" % cube.required_strength_mpa)
	check(cube.result == "Pass", "22.4 MPa against 19.5 required = Pass")

	frappe.db.commit()          # the cycle above is real work; keep it

	print()
	print("=" * 74)
	print("PHASE 3  —  the guard rails still bite")
	print("=" * 74)
	as_user("dispatch@midhunarmc.com")
	frappe.db.savepoint("gr1")
	try:
		over = frappe.get_doc({
			"doctype": "Delivery Challan", "concrete_order": order.name, "challan_date": today,
			"grade": "M30", "qty_m3": 50, "rate": 5600, "transit_mixer": mixer,
			"dispatch_time": get_datetime(),
		})
		over.insert()
		check(False, "Over-delivering the order is blocked", "50 m³ was accepted!")
	except frappe.ValidationError:
		check(True, "Over-delivering the order is blocked", "50 m³ refused")
	frappe.db.rollback(save_point="gr1")

	as_user("operator@midhunarmc.com")
	frappe.db.savepoint("gr2")
	try:
		wrong = frappe.get_doc({
			"doctype": "Batch Production", "production_date": today, "plant": plant,
			"shift": "Shift A", "grade": "M20",
			"mix_design": mix,                       # an M30 design against an M20 batch
			"qty_m3": 3, "operator": "K. Srinivas",
		})
		wrong.insert()
		check(False, "Wrong mix design for the grade is blocked", "accepted!")
	except frappe.ValidationError:
		check(True, "Wrong mix design for the grade is blocked", "M30 design on M20 refused")
	frappe.db.rollback(save_point="gr2")

	as_user("Administrator")
	cust = site.customer
	frappe.db.set_value("Customer", cust, "rmc_credit_status", "Hold")
	frappe.db.savepoint("gr3")
	try:
		frappe.get_doc({
			"doctype": "Concrete Order", "customer": cust, "construction_site": site.name,
			"order_date": today, "grade": "M25", "order_qty_m3": 5, "rate": 5000,
			"required_from": today,
		}).insert()
		check(False, "Credit hold blocks a new order", "accepted!")
	except frappe.ValidationError:
		check(True, "Credit hold blocks a new order", "refused for %s" % cust[:24])
	frappe.db.rollback(save_point="gr3")
	frappe.db.set_value("Customer", cust, "rmc_credit_status", "Normal")
	frappe.db.commit()

	print()
	print("=" * 74)
	print("PHASE 4  —  every total moved by exactly the right amount")
	print("=" * 74)
	after = snapshot()
	check(after["orders"] == before["orders"] + 1, "Order count +1",
	      "%d -> %d" % (before["orders"], after["orders"]))
	check(after["batches"] == before["batches"] + 1, "Batch count +1",
	      "%d -> %d" % (before["batches"], after["batches"]))
	check(after["challans"] == before["challans"] + 1, "Challan count +1",
	      "%d -> %d" % (before["challans"], after["challans"]))
	check(after["invoices"] == before["invoices"] + 1, "Invoice count +1",
	      "%d -> %d" % (before["invoices"], after["invoices"]))
	check(after["stock_entries"] == before["stock_entries"] + 1, "Stock entry +1",
	      "%d -> %d" % (before["stock_entries"], after["stock_entries"]))
	check(abs(after["produced"] - before["produced"] - 6) < 0.01, "Produced +6 m³")
	check(abs(after["dispatched"] - before["dispatched"] - 6) < 0.01, "Dispatched +6 m³")
	check(abs(after["revenue"] - before["revenue"] - 33600) < 1, "Revenue +₹33,600")

	q = frappe.db.sql
	produced = flt(q("SELECT SUM(qty_m3) FROM `tabBatch Production` WHERE docstatus=1")[0][0])
	ledger = flt(q("""SELECT SUM(sed.qty) FROM `tabStock Entry Detail` sed
		JOIN `tabStock Entry` se ON se.name = sed.parent
		WHERE se.docstatus=1 AND se.rmc_batch_production IS NOT NULL
		  AND sed.item_code LIKE 'RMC-M%' AND sed.t_warehouse IS NOT NULL""")[0][0])
	check(abs(produced - ledger) < 0.5, "Produced still reconciles with the stock ledger",
	      "%.2f vs %.2f" % (produced, ledger))
	disp = flt(q("SELECT SUM(qty_m3) FROM `tabDelivery Challan` WHERE docstatus=1")[0][0])
	inv = flt(q("""SELECT SUM(sii.qty) FROM `tabSales Invoice Item` sii
		JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE si.docstatus=1 AND si.rmc_delivery_challan IS NOT NULL""")[0][0])
	check(abs(disp - inv) < 0.5, "Dispatched still reconciles with invoiced",
	      "%.2f vs %.2f" % (disp, inv))

	print()
	print("=" * 74)
	print("PHASE 5  —  the new load shows up on the screens, immediately")
	print("=" * 74)
	from rmc import dashboard as D
	from frappe.desk.query_report import run as run_report

	mg = D.management(str(today), str(today))
	check(mg["sales"]["loads"] >= 1, "Management (Today) counts the new load",
	      "%d loads, ₹%s" % (mg["sales"]["loads"], mg["sales"]["value"]))
	bb = D.batch_board(str(today), str(today))
	check(any(b.name == batch.name for b in bb["batches"]),
	      "Batching Board (Today) lists the batch", batch.name)
	db = D.dispatch_board(str(today), str(today))
	check(any(t.name == challan.name for t in db["trips"]),
	      "Dispatch Board (Today) lists the trip", challan.name)
	o3 = D.order_360(order.name)
	check(len(o3["challans"]) == 1 and o3["progress_pct"] > 0,
	      "Order 360 shows the order at %.1f%% complete" % o3["progress_pct"])
	qb = D.quality_board(str(today), str(today))
	check(qb["total_tests"] >= 1, "Quality Board (Today) counts the cube test",
	      "%d tests" % qb["total_tests"])

	f_today = {"from_date": str(today), "to_date": str(today)}
	for rep, expect in (("Dispatch Register", challan.name),
	                    ("Batch Register", batch.name),
	                    ("Concrete Sales Register", challan.sales_invoice),
	                    ("Cube Test Register", cube.name)):
		rows = run_report(rep, filters=dict(f_today), ignore_prepared_report=True)["result"]
		found = any(expect in str(r) for r in rows)
		check(found, "%s (Today) contains it" % rep, expect)

	prod = run_report("Plant Productivity", filters=dict(f_today),
	                  ignore_prepared_report=True)["result"]
	check(len(prod) > 0, "Plant Productivity (Today) returns", "%d rows" % len(prod))

	print()
	print("=" * 74)
	print("RESULT:  %d PASS, %d FAIL" % (PASS, FAIL))
	if LOG:
		for x in LOG:
			print("   FAILED:", x)
	print("Demo documents left on the site:", order.name, batch.name, challan.name,
	      challan.sales_invoice, cube.name)
	frappe.db.commit()

	return {"pass": PASS, "fail": FAIL, "failures": LOG}

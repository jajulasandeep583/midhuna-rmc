"""Server side of the RMC desk pages.

One whitelisted call per board, each returning everything that board needs, so
the page renders from a single round trip instead of a dozen list queries.
"""

import frappe
from frappe.utils import add_days, flt, getdate, nowdate


def _plant():
	return frappe.db.get_single_value("RMC Settings", "default_plant")


@frappe.whitelist()
def management(from_date=None, to_date=None, plant=None):
	"""One page for the owner: what we sold, what we bought, what we hold, what
	we made, and who owes us — for any period."""
	to_date = getdate(to_date or nowdate())
	from_date = getdate(from_date or add_days(to_date, -29))
	rng = {"from_date": from_date, "to_date": to_date}

	plant_cond = " AND bp.plant = %(plant)s" if plant else ""
	if plant:
		rng["plant"] = plant

	sales = frappe.db.sql("""
		SELECT COUNT(dc.name) loads, SUM(dc.qty_m3) qty, SUM(dc.amount) value,
		       COUNT(DISTINCT dc.customer) customers
		FROM `tabDelivery Challan` dc
		WHERE dc.docstatus = 1 AND dc.challan_date BETWEEN %(from_date)s AND %(to_date)s
	""", rng, as_dict=True)[0]

	production = frappe.db.sql("""
		SELECT COUNT(bp.name) batches, SUM(bp.qty_m3) qty,
		       SUM(bp.total_material_cost) cost
		FROM `tabBatch Production` bp
		WHERE bp.docstatus = 1
		  AND bp.production_date BETWEEN %(from_date)s AND %(to_date)s {plant}
	""".format(plant=plant_cond), rng, as_dict=True)[0]

	purchase = frappe.db.sql("""
		SELECT COUNT(mi.name) trucks, SUM(mi.net_weight) mt, SUM(mi.amount) value,
		       COUNT(DISTINCT mi.supplier) suppliers
		FROM `tabMaterial Inward` mi
		WHERE mi.docstatus = 1 AND mi.inward_date BETWEEN %(from_date)s AND %(to_date)s
	""", rng, as_dict=True)[0]

	top_customers = frappe.db.sql("""
		SELECT dc.customer, SUM(dc.qty_m3) qty, SUM(dc.amount) value, COUNT(*) loads
		FROM `tabDelivery Challan` dc
		WHERE dc.docstatus = 1 AND dc.challan_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY dc.customer ORDER BY SUM(dc.amount) DESC LIMIT 8
	""", rng, as_dict=True)

	by_grade = frappe.db.sql("""
		SELECT dc.grade, SUM(dc.qty_m3) qty, SUM(dc.amount) value
		FROM `tabDelivery Challan` dc
		WHERE dc.docstatus = 1 AND dc.challan_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY dc.grade ORDER BY SUM(dc.qty_m3) DESC
	""", rng, as_dict=True)

	top_materials = frappe.db.sql("""
		SELECT mi.item_code, mi.material_type, SUM(mi.net_weight) mt, SUM(mi.amount) value
		FROM `tabMaterial Inward` mi
		WHERE mi.docstatus = 1 AND mi.inward_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY mi.item_code, mi.material_type ORDER BY SUM(mi.amount) DESC LIMIT 8
	""", rng, as_dict=True)

	daily = frappe.db.sql("""
		SELECT d, SUM(produced) produced, SUM(dispatched) dispatched, SUM(value) value FROM (
			SELECT production_date d, SUM(qty_m3) produced, 0 dispatched, 0 value
			FROM `tabBatch Production` WHERE docstatus = 1
			  AND production_date BETWEEN %(from_date)s AND %(to_date)s
			GROUP BY production_date
			UNION ALL
			SELECT challan_date d, 0, SUM(qty_m3), SUM(amount)
			FROM `tabDelivery Challan` WHERE docstatus = 1
			  AND challan_date BETWEEN %(from_date)s AND %(to_date)s
			GROUP BY challan_date
		) x GROUP BY d ORDER BY d
	""", rng, as_dict=True)

	# what customers still owe, straight out of the GL
	receivables = frappe.db.sql("""
		SELECT si.customer, SUM(si.grand_total) billed, SUM(si.outstanding_amount) outstanding
		FROM `tabSales Invoice` si
		WHERE si.docstatus = 1
		GROUP BY si.customer HAVING SUM(si.outstanding_amount) > 0
		ORDER BY SUM(si.outstanding_amount) DESC LIMIT 8
	""", as_dict=True)

	stock = frappe.db.sql("""
		SELECT i.item_group, SUM(b.actual_qty) qty, SUM(b.stock_value) value
		FROM `tabBin` b JOIN `tabItem` i ON i.name = b.item_code
		GROUP BY i.item_group ORDER BY SUM(b.stock_value) DESC
	""", as_dict=True)

	revenue = flt(sales.value)
	mat_cost = flt(production.cost)
	return {
		"period": {"from": str(from_date), "to": str(to_date)},
		"sales": {"loads": sales.loads or 0, "qty": round(flt(sales.qty), 2),
		          "value": round(revenue, 2), "customers": sales.customers or 0,
		          "avg_rate": round(revenue / flt(sales.qty), 2) if flt(sales.qty) else 0},
		"production": {"batches": production.batches or 0,
		               "qty": round(flt(production.qty), 2),
		               "cost": round(mat_cost, 2),
		               "cost_per_m3": round(mat_cost / flt(production.qty), 2)
		               if flt(production.qty) else 0},
		"purchase": {"trucks": purchase.trucks or 0, "mt": round(flt(purchase.mt), 2),
		             "value": round(flt(purchase.value), 2),
		             "suppliers": purchase.suppliers or 0},
		"margin": {"revenue": round(revenue, 2), "material_cost": round(mat_cost, 2),
		           "gross": round(revenue - mat_cost, 2),
		           "pct": round(100.0 * (revenue - mat_cost) / revenue, 1) if revenue else 0},
		"top_customers": top_customers, "by_grade": by_grade,
		"top_materials": top_materials, "daily": daily,
		"receivables": receivables,
		"receivable_total": round(sum(flt(r.outstanding) for r in receivables), 2),
		"stock": stock,
		"stock_value": round(sum(flt(s.value) for s in stock), 2),
		"open_orders": frappe.db.count("Concrete Order",
		                               {"docstatus": 1,
		                                "status": ["in", ["Open", "In Progress"]]}),
		"pending_m3": round(flt(frappe.db.sql("""
			SELECT SUM(pending_qty_m3) FROM `tabConcrete Order`
			WHERE docstatus = 1 AND status IN ('Open','In Progress')""")[0][0]), 2),
		"low_silos": [s for s in silo_board() if s["low"]],
	}


@frappe.whitelist()
def control_tower(days=7, plant=None):
	"""The morning view: yesterday and today, orders in hand, plant health."""
	days = int(days)
	today = getdate(nowdate())
	start = add_days(today, -(days - 1))

	pc = " AND plant = %(plant)s" if plant else ""
	args = {"start": start, "plant": plant}
	trend = frappe.db.sql("""
		SELECT production_date d, SUM(qty_m3) q FROM `tabBatch Production`
		WHERE docstatus = 1 AND production_date >= %(start)s""" + pc + """
		GROUP BY production_date""", args, as_dict=True)
	disp = frappe.db.sql("""
		SELECT challan_date d, SUM(qty_m3) q, SUM(amount) v, COUNT(name) trips
		FROM `tabDelivery Challan`
		WHERE docstatus = 1 AND challan_date >= %(start)s
		GROUP BY challan_date""", args, as_dict=True)

	pmap = {str(r.d): flt(r.q) for r in trend}
	dmap = {str(r.d): r for r in disp}
	series = []
	for i in range(days):
		d = str(add_days(start, i))
		row = dmap.get(d)
		series.append({
			"date": d,
			"produced": round(pmap.get(d, 0), 2),
			"dispatched": round(flt(row.q) if row else 0, 2),
			"trips": (row.trips if row else 0),
			"value": round(flt(row.v) if row else 0, 2),
		})

	grades = frappe.db.sql("""
		SELECT grade, SUM(qty_m3) q FROM `tabBatch Production`
		WHERE docstatus = 1 AND production_date >= %(start)s""" + pc + """
		GROUP BY grade ORDER BY q DESC""", args, as_dict=True)

	return {
		"plant": plant or _plant(),
		"period": {"from": str(start), "to": str(today)},
		"series": series,
		"grades": [{"grade": g.grade, "qty": round(flt(g.q), 2)} for g in grades],
		"today": series[-1] if series else {},
		"open_orders": frappe.db.count("Concrete Order",
		                               {"docstatus": 1,
		                                "status": ["in", ["Open", "In Progress"]]}),
		"pending_m3": round(flt(frappe.db.sql("""
			SELECT SUM(pending_qty_m3) FROM `tabConcrete Order`
			WHERE docstatus = 1 AND status IN ('Open','In Progress')""")[0][0]), 2),
		"low_silos": len([s for s in silo_board() if s["low"]]),
		"open_breakdowns": frappe.db.count("Breakdown Log",
		                                   {"status": ["in", ["Open", "In Progress"]]}),
		"failed_cubes": frappe.db.count("Cube Test", {"docstatus": 1, "result": "Fail"}),
		"maintenance_due": frappe.db.count("RMC Maintenance Task",
		                                   {"status": ["in", ["Due", "Overdue"]]}),
	}


@frappe.whitelist()
def batch_board(from_date=None, to_date=None, shift=None, grade=None, plant=None,
                date=None):
	"""Batching over a date range, by shift, with material consumption.

	`date` is still accepted so an old bookmark or link keeps working.
	"""
	if date and not from_date:
		from_date = to_date = date
	to_date = getdate(to_date or nowdate())
	from_date = getdate(from_date or to_date)

	extra = ((" AND bp.shift = %(shift)s" if shift else "")
	         + (" AND bp.grade = %(grade)s" if grade else "")
	         + (" AND bp.plant = %(plant)s" if plant else ""))
	args = {"from_date": from_date, "to_date": to_date, "shift": shift,
	        "grade": grade, "plant": plant}

	batches = frappe.db.sql("""
		SELECT bp.name, bp.production_date, bp.shift, bp.grade, bp.qty_m3,
		       bp.no_of_batches, bp.operator, bp.start_time, bp.end_time,
		       bp.cost_per_m3, bp.concrete_order, co.customer, bp.stock_entry, bp.status
		FROM `tabBatch Production` bp
		LEFT JOIN `tabConcrete Order` co ON co.name = bp.concrete_order
		WHERE bp.docstatus = 1
		  AND bp.production_date BETWEEN %(from_date)s AND %(to_date)s""" + extra + """
		ORDER BY bp.production_date DESC, bp.start_time""", args, as_dict=True)

	materials = frappe.db.sql("""
		SELECT bm.item_code, bm.material_type, SUM(bm.target_qty) target,
		       SUM(bm.actual_qty) actual, SUM(bm.amount) cost, bm.uom
		FROM `tabBatch Material` bm
		JOIN `tabBatch Production` bp ON bp.name = bm.parent
		WHERE bp.docstatus = 1
		  AND bp.production_date BETWEEN %(from_date)s AND %(to_date)s""" + extra + """
		GROUP BY bm.item_code, bm.material_type, bm.uom
		ORDER BY SUM(bm.amount) DESC""", args, as_dict=True)

	for m in materials:
		m["variance_pct"] = round(
			100.0 * (flt(m.actual) - flt(m.target)) / flt(m.target), 2) if flt(m.target) else 0

	shifts, days = {}, {}
	for b in batches:
		sh = shifts.setdefault(b.shift, {"loads": 0, "qty": 0})
		sh["loads"] += 1
		sh["qty"] += flt(b.qty_m3)
		days[str(b.production_date)] = days.get(str(b.production_date), 0) + flt(b.qty_m3)

	return {
		"from_date": str(from_date), "to_date": str(to_date),
		"batches": batches, "materials": materials,
		"shifts": [{"shift": k, **v} for k, v in sorted(shifts.items())],
		"days": [{"date": k, "qty": round(v, 2)} for k, v in sorted(days.items())],
		"total_qty": round(sum(flt(b.qty_m3) for b in batches), 2),
		"total_cost": round(sum(flt(b.qty_m3) * flt(b.cost_per_m3) for b in batches), 2),
	}



@frappe.whitelist()
def dispatch_board(from_date=None, to_date=None, customer=None, status=None,
                   transit_mixer=None, grade=None, date=None):
	"""Trips over a date range: who went out, who is back, how long the cycle took."""
	if date and not from_date:
		from_date = to_date = date
	to_date = getdate(to_date or nowdate())
	from_date = getdate(from_date or to_date)

	extra = ((" AND dc.customer = %(customer)s" if customer else "")
	         + (" AND dc.status = %(status)s" if status else "")
	         + (" AND dc.transit_mixer = %(transit_mixer)s" if transit_mixer else "")
	         + (" AND dc.grade = %(grade)s" if grade else ""))
	args = {"from_date": from_date, "to_date": to_date, "customer": customer,
	        "status": status, "transit_mixer": transit_mixer, "grade": grade}

	trips = frappe.db.sql("""
		SELECT dc.name, dc.challan_date, dc.customer, cs.site_name, dc.grade, dc.qty_m3,
		       dc.amount, dc.transit_mixer, dc.driver_name, dc.dispatch_time,
		       dc.site_arrival_time, dc.return_time, dc.cycle_time_min, dc.slump_mm,
		       dc.status, dc.sales_invoice, cs.distance_km
		FROM `tabDelivery Challan` dc
		LEFT JOIN `tabConstruction Site` cs ON cs.name = dc.construction_site
		WHERE dc.docstatus = 1
		  AND dc.challan_date BETWEEN %(from_date)s AND %(to_date)s""" + extra + """
		ORDER BY dc.challan_date DESC, dc.dispatch_time DESC""", args, as_dict=True)

	fleet = frappe.get_all("Transit Mixer", filters={"vehicle_type": "Transit Mixer"},
	                       fields=["name", "capacity_m3", "status", "ownership"],
	                       order_by="name")
	cycles = [t.cycle_time_min for t in trips if t.cycle_time_min]
	days = {}
	for t in trips:
		days[str(t.challan_date)] = days.get(str(t.challan_date), 0) + flt(t.qty_m3)

	return {
		"from_date": str(from_date), "to_date": str(to_date),
		"trips": trips, "fleet": fleet,
		"days": [{"date": k, "qty": round(v, 2)} for k, v in sorted(days.items())],
		"total_qty": round(sum(flt(t.qty_m3) for t in trips), 2),
		"total_value": round(sum(flt(t.amount) for t in trips), 2),
		"avg_cycle": round(sum(cycles) / len(cycles), 1) if cycles else 0,
		"on_trip": sum(1 for f in fleet if f.status == "On Trip"),
		"available": sum(1 for f in fleet if f.status == "Available"),
	}



@frappe.whitelist()
def order_360(order):
	"""One order end to end: schedule, batches, challans and invoices."""
	doc = frappe.get_doc("Concrete Order", order)
	challans = frappe.get_all(
		"Delivery Challan", filters={"concrete_order": order, "docstatus": 1},
		fields=["name", "challan_date", "qty_m3", "amount", "transit_mixer",
		        "driver_name", "dispatch_time", "cycle_time_min", "slump_mm",
		        "status", "sales_invoice", "batch_production"],
		order_by="challan_date desc, dispatch_time desc")
	batches = frappe.get_all(
		"Batch Production", filters={"concrete_order": order, "docstatus": 1},
		fields=["name", "production_date", "shift", "qty_m3", "cost_per_m3",
		        "operator", "stock_entry"],
		order_by="production_date desc")
	cubes = frappe.get_all(
		"Cube Test", filters={"delivery_challan": ["in", [c.name for c in challans] or [""]]},
		fields=["name", "casting_date", "age_days", "avg_strength_mpa",
		        "required_strength_mpa", "result"])
	invoiced = flt(frappe.db.sql("""
		SELECT SUM(si.net_total) FROM `tabSales Invoice` si
		WHERE si.docstatus = 1 AND si.po_no = %s""", order)[0][0])

	return {
		"order": doc.as_dict(),
		"site": frappe.db.get_value("Construction Site", doc.construction_site,
		                            ["site_name", "site_address", "distance_km",
		                             "contact_person", "contact_no"], as_dict=True),
		"challans": challans, "batches": batches, "cubes": cubes,
		"invoiced_value": round(invoiced, 2),
		"progress_pct": round(100.0 * flt(doc.delivered_qty_m3) / flt(doc.order_qty_m3), 1)
		if flt(doc.order_qty_m3) else 0,
	}


@frappe.whitelist()
def silo_board(material_type=None, only_low=None):
	"""Live level of every silo, with days of cover at the recent burn rate."""
	out = []
	silo_filters = {"is_active": 1}
	if material_type:
		silo_filters["material_type"] = material_type
	for s in frappe.get_all("Silo", filters=silo_filters,
	                        fields=["name", "silo_name", "material_type", "item_code",
	                                "warehouse", "capacity_mt", "min_level_mt"],
	                        order_by="material_type, silo_name"):
		qty = flt(frappe.db.get_value("Bin", {"item_code": s.item_code,
		                                      "warehouse": s.warehouse}, "actual_qty"))
		stock = qty / 1000.0
		burn = flt(frappe.db.sql("""
			SELECT SUM(bm.actual_qty) FROM `tabBatch Material` bm
			JOIN `tabBatch Production` bp ON bp.name = bm.parent
			WHERE bp.docstatus = 1 AND bm.item_code = %s
			  AND bp.production_date >= %s""",
			(s.item_code, add_days(getdate(nowdate()), -7)))[0][0]) / 7000.0
		row = {
			"silo": s.silo_name, "material": s.material_type, "item": s.item_code,
			"stock_mt": round(stock, 2), "capacity_mt": flt(s.capacity_mt),
			"filled_pct": round(100.0 * stock / flt(s.capacity_mt), 1)
			if flt(s.capacity_mt) else 0,
			"min_level": flt(s.min_level_mt),
			"low": bool(s.min_level_mt and stock <= flt(s.min_level_mt)),
			"daily_burn_mt": round(burn, 2),
			"days_cover": round(stock / burn, 1) if burn else None,
		}
		if only_low and not row["low"]:
			continue
		out.append(row)
	return out


@frappe.whitelist()
def quality_board(from_date=None, to_date=None, grade=None, days=None):
	"""Cube tests over a range, pass rate by grade, and 28-day breaks still pending."""
	to_date = getdate(to_date or nowdate())
	from_date = getdate(from_date or add_days(to_date, -(int(days) if days else 90)))
	args = {"from_date": from_date, "to_date": to_date, "grade": grade}
	gc = " AND grade = %(grade)s" if grade else ""

	by_grade = frappe.db.sql("""
		SELECT grade, COUNT(*) tests,
		       SUM(CASE WHEN result = 'Pass' THEN 1 ELSE 0 END) passed,
		       AVG(avg_strength_mpa) avg_strength, AVG(strength_pct) avg_pct
		FROM `tabCube Test`
		WHERE docstatus = 1 AND casting_date BETWEEN %(from_date)s AND %(to_date)s""" + gc + """
		GROUP BY grade ORDER BY grade""", args, as_dict=True)
	for g in by_grade:
		g["pass_rate"] = round(100.0 * g.passed / g.tests, 1) if g.tests else 0
		g["avg_strength"] = round(flt(g.avg_strength), 1)
		g["avg_pct"] = round(flt(g.avg_pct), 1)

	fails = frappe.db.sql("""
		SELECT name, casting_date, grade, age_days, avg_strength_mpa,
		       required_strength_mpa, batch_production, delivery_challan
		FROM `tabCube Test`
		WHERE docstatus = 1 AND result = 'Fail'
		  AND casting_date BETWEEN %(from_date)s AND %(to_date)s""" + gc + """
		ORDER BY casting_date DESC""", args, as_dict=True)

	pending = frappe.db.sql("""
		SELECT dc.name, dc.challan_date, dc.grade, dc.qty_m3, dc.batch_production
		FROM `tabDelivery Challan` dc
		WHERE dc.docstatus = 1 AND dc.cubes_taken = 1
		  AND dc.challan_date BETWEEN %(from_date)s AND %(to_date)s
		  AND NOT EXISTS (SELECT 1 FROM `tabCube Test` ct
		                  WHERE ct.docstatus = 1 AND ct.delivery_challan = dc.name
		                    AND ct.age_days = '28')
		ORDER BY dc.challan_date DESC LIMIT 40""", args, as_dict=True)

	slumps = frappe.db.sql("""
		SELECT slump_mm, COUNT(*) n FROM `tabDelivery Challan`
		WHERE docstatus = 1 AND IFNULL(slump_mm,0) > 0
		  AND challan_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY slump_mm ORDER BY slump_mm""", args, as_dict=True)

	return {"from_date": str(from_date), "to_date": str(to_date),
	        "by_grade": by_grade, "fails": fails, "pending_28day": pending,
	        "slumps": slumps,
	        "total_tests": sum(g.tests for g in by_grade),
	        "total_fails": len(fails)}



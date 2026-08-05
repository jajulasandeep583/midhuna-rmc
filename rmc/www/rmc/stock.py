"""Public stock page — what is in every silo right now, and what it is worth."""

import frappe
from frappe.utils import add_days, flt, getdate, nowdate

from rmc.www.rmc.index import common, money

no_cache = 1


def get_context(context):
	frm, to = common(context)
	context.title = "Stock"

	silos = frappe.db.sql("""
		SELECT s.silo_name, s.material_type, s.item_code, s.capacity_mt, s.min_level_mt,
		       s.plant, IFNULL(b.actual_qty, 0) qty, IFNULL(b.stock_value, 0) value,
		       IFNULL(b.valuation_rate, 0) rate
		FROM `tabSilo` s
		LEFT JOIN `tabBin` b ON b.warehouse = s.warehouse AND b.item_code = s.item_code
		WHERE s.is_active = 1 ORDER BY s.material_type, s.silo_name""", as_dict=True)

	week_ago = add_days(getdate(nowdate()), -7)
	for s in silos:
		s.stock = round(flt(s.qty) / 1000.0, 2)
		s.pct = round(100.0 * s.stock / flt(s.capacity_mt), 1) if flt(s.capacity_mt) else 0
		s.low = bool(s.min_level_mt and s.stock <= flt(s.min_level_mt))
		s.value_h = money(s.value)
		burn = flt(frappe.db.sql("""
			SELECT SUM(bm.actual_qty) FROM `tabBatch Material` bm
			JOIN `tabBatch Production` bp ON bp.name = bm.parent
			WHERE bp.docstatus = 1 AND bm.item_code = %s AND bp.production_date >= %s""",
			(s.item_code, week_ago))[0][0]) / 7000.0
		s.burn = round(burn, 2)
		s.cover = round(s.stock / burn, 1) if burn else None

	context.silos = silos
	context.low = [s for s in silos if s.low]
	context.stock_value_h = money(sum(flt(s.value) for s in silos))

	finished = frappe.db.sql("""
		SELECT b.item_code, b.actual_qty, b.stock_value FROM `tabBin` b
		JOIN `tabItem` i ON i.name = b.item_code
		WHERE i.item_group = 'Ready Mix Concrete' AND b.actual_qty <> 0""", as_dict=True)
	context.finished = finished
	context.finished_value_h = money(sum(flt(f.stock_value) for f in finished))

	inward = frappe.db.sql("""
		SELECT material_type, COUNT(*) trucks, SUM(net_weight) mt, SUM(amount) value
		FROM `tabMaterial Inward`
		WHERE docstatus = 1 AND inward_date BETWEEN %(f)s AND %(t)s
		GROUP BY material_type ORDER BY SUM(amount) DESC""", {"f": frm, "t": to}, as_dict=True)
	for i in inward:
		i.value_h = money(i.value)
	context.inward = inward
	context.inward_value_h = money(sum(flt(i.value) for i in inward))
	context.inward_trucks = sum(i.trucks for i in inward)

	context.kpis = [
		("Raw material in stock", "₹ " + context.stock_value_h,
		 "%d silos and yards" % len(silos), "buy"),
		("Finished concrete", "₹ " + context.finished_value_h,
		 "%d grades held" % len(finished), "prod"),
		("Bought this period", "₹ " + context.inward_value_h,
		 "%d trucks weighed in" % context.inward_trucks, "sale"),
		("Silos below alert", len(context.low),
		 "of %d" % len(silos), "pl"),
	]

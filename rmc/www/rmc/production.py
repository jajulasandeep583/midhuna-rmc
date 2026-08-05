"""Public production page — what the plant made, and what it consumed doing it."""

import frappe
from frappe.utils import flt

from rmc.www.rmc.index import common, money

no_cache = 1


def get_context(context):
	frm, to = common(context)
	context.title = "Production"

	head = frappe.db.sql("""
		SELECT COUNT(*) batches, SUM(qty_m3) qty, SUM(no_of_batches) mixes,
		       SUM(total_material_cost) cost, COUNT(DISTINCT production_date) days
		FROM `tabBatch Production`
		WHERE docstatus = 1 AND production_date BETWEEN %(f)s AND %(t)s""",
		{"f": frm, "t": to}, as_dict=True)[0]
	qty = flt(head.qty)

	run_hours = flt(frappe.db.sql("""
		SELECT SUM(duration_hours) FROM `tabPlant Status Log`
		WHERE status = 'Running' AND log_date BETWEEN %(f)s AND %(t)s""",
		{"f": frm, "t": to})[0][0])

	context.kpis = [
		("Produced", "%s m³" % qty, "%d loads over %d days" % (head.batches or 0, head.days or 0),
		 "prod"),
		("Material cost", "₹ " + money(head.cost), "₹ %s per m³"
		 % money(flt(head.cost) / qty if qty else 0), "buy"),
		("Running hours", "%s h" % round(run_hours, 1), "%s m³ per running hour"
		 % round(qty / run_hours, 2) if run_hours else "no plant log", "prod"),
		("Mixes batched", head.mixes or 0, "%s m³ average per load"
		 % round(qty / head.batches, 2) if head.batches else "—", "sale"),
	]

	context.by_grade = frappe.db.sql("""
		SELECT grade, COUNT(*) loads, SUM(qty_m3) qty,
		       SUM(total_material_cost)/NULLIF(SUM(qty_m3),0) cost_per_m3
		FROM `tabBatch Production`
		WHERE docstatus = 1 AND production_date BETWEEN %(f)s AND %(t)s
		GROUP BY grade ORDER BY SUM(qty_m3) DESC""", {"f": frm, "t": to}, as_dict=True)
	peak = flt(max([g.qty for g in context.by_grade], default=1))
	for g in context.by_grade:
		g.pct = round(100.0 * flt(g.qty) / peak, 1)
		g.cost_h = money(g.cost_per_m3)

	context.by_shift = frappe.db.sql("""
		SELECT shift, COUNT(*) loads, SUM(qty_m3) qty
		FROM `tabBatch Production`
		WHERE docstatus = 1 AND production_date BETWEEN %(f)s AND %(t)s
		GROUP BY shift ORDER BY shift""", {"f": frm, "t": to}, as_dict=True)

	context.materials = frappe.db.sql("""
		SELECT bm.item_code, bm.material_type, bm.uom,
		       SUM(bm.target_qty) target, SUM(bm.actual_qty) actual, SUM(bm.amount) cost
		FROM `tabBatch Material` bm JOIN `tabBatch Production` bp ON bp.name = bm.parent
		WHERE bp.docstatus = 1 AND bp.production_date BETWEEN %(f)s AND %(t)s
		GROUP BY bm.item_code, bm.material_type, bm.uom
		ORDER BY SUM(bm.amount) DESC""", {"f": frm, "t": to}, as_dict=True)
	for m in context.materials:
		m.var = round(100.0 * (flt(m.actual) - flt(m.target)) / flt(m.target), 2) if flt(m.target) else 0
		m.cost_h = money(m.cost)
		m.per_m3 = round(flt(m.actual) / qty, 2) if qty else 0

	context.daily = frappe.db.sql("""
		SELECT production_date d, SUM(qty_m3) qty FROM `tabBatch Production`
		WHERE docstatus = 1 AND production_date BETWEEN %(f)s AND %(t)s
		GROUP BY production_date ORDER BY production_date""", {"f": frm, "t": to}, as_dict=True)
	top = flt(max([d.qty for d in context.daily], default=1))
	for d in context.daily:
		d.pct = round(100.0 * flt(d.qty) / top, 1)

	context.cubes = frappe.db.sql("""
		SELECT grade, COUNT(*) tests,
		       SUM(CASE WHEN result='Pass' THEN 1 ELSE 0 END) passed,
		       ROUND(AVG(avg_strength_mpa),1) avg_mpa
		FROM `tabCube Test`
		WHERE docstatus = 1 AND casting_date BETWEEN %(f)s AND %(t)s
		GROUP BY grade ORDER BY grade""", {"f": frm, "t": to}, as_dict=True)

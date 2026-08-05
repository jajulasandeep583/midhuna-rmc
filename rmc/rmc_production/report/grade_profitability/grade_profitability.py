# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""What each grade earns after the material it consumes."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	where, params = build_conditions(
		filters, {"grade": "dc.grade"}, date_field="challan_date", alias="dc")

	sold = frappe.db.sql("""
		SELECT dc.grade, SUM(dc.qty_m3) qty, SUM(dc.amount) value, COUNT(*) loads
		FROM `tabDelivery Challan` dc
		WHERE dc.docstatus = 1 AND {where}
		GROUP BY dc.grade
	""".format(where=where), params, as_dict=True)

	pwhere, pparams = build_conditions(
		filters, {"grade": "bp.grade"}, date_field="production_date", alias="bp")
	made = {r.grade: r for r in frappe.db.sql("""
		SELECT bp.grade, SUM(bp.qty_m3) qty, SUM(bp.total_material_cost) cost
		FROM `tabBatch Production` bp
		WHERE bp.docstatus = 1 AND {where}
		GROUP BY bp.grade
	""".format(where=pwhere), pparams, as_dict=True)}

	data = []
	for s in sold:
		m = made.get(s.grade)
		cost_per_m3 = (flt(m.cost) / flt(m.qty)) if m and flt(m.qty) else 0
		rate = flt(s.value) / flt(s.qty) if flt(s.qty) else 0
		cost = cost_per_m3 * flt(s.qty)
		margin = flt(s.value) - cost
		data.append([s.grade, s.loads, flt(s.qty), rate, flt(s.value), cost_per_m3,
		             cost, margin, (100.0 * margin / flt(s.value)) if flt(s.value) else 0])
	data.sort(key=lambda r: -r[7])

	columns = [
		col("Grade", "Link", 90, options="Concrete Grade"),
		col("Loads", "Int", 80), col("Sold m3", "Float", 105, precision=2),
		col("Avg Rate", "Currency", 115), col("Revenue", "Currency", 135),
		col("Cost per m3", "Currency", 120), col("Material Cost", "Currency", 135),
		col("Gross Margin", "Currency", 135), col("Margin Pct", "Percent", 105),
	]

	chart = {"data": {"labels": [d[0] for d in data],
	                  "datasets": [{"name": "Gross margin",
	                                "values": [round(d[7], 0) for d in data]}]},
	         "type": "bar", "colors": ["#0F766E"]}

	rev = sum(d[4] for d in data)
	marg = sum(d[7] for d in data)
	summary = [
		{"label": "Revenue", "value": round(rev, 2), "datatype": "Currency",
		 "indicator": "Green"},
		{"label": "Gross margin", "value": round(marg, 2), "datatype": "Currency",
		 "indicator": "Blue"},
		{"label": "Margin", "value": round(100.0 * marg / rev, 1) if rev else 0,
		 "datatype": "Percent", "indicator": "Orange"},
	]
	return columns, data, None, chart, summary

# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""How much of each grade was poured, per day and shift, and at what cost."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	where, params = build_conditions(
		filters, {"plant": "bp.plant", "grade": "bp.grade", "shift": "bp.shift"},
		date_field="production_date", alias="bp")

	rows = frappe.db.sql("""
		SELECT bp.production_date, bp.shift, bp.grade,
		       COUNT(bp.name) loads, SUM(bp.no_of_batches) batches,
		       SUM(bp.qty_m3) produced, SUM(bp.total_material_cost) cost
		FROM `tabBatch Production` bp
		WHERE bp.docstatus = 1 AND {where}
		GROUP BY bp.production_date, bp.shift, bp.grade
		ORDER BY bp.production_date DESC, bp.shift, bp.grade
	""".format(where=where), params, as_dict=True)

	data = []
	by_day = {}
	for r in rows:
		cost_per_m3 = flt(r.cost) / flt(r.produced) if flt(r.produced) else 0
		data.append([r.production_date, r.shift, r.grade, r.loads, r.batches,
		             flt(r.produced), flt(r.cost), cost_per_m3])
		by_day[r.production_date] = by_day.get(r.production_date, 0) + flt(r.produced)

	columns = [
		col("Date", "Date", 100), col("Shift", "Data", 90),
		col("Grade", "Link", 80, options="Concrete Grade"),
		col("Loads", "Int", 70), col("Batches", "Int", 80),
		col("Produced m3", "Float", 115, precision=2),
		col("Material Cost", "Currency", 130),
		col("Cost per m3", "Currency", 120),
	]

	days = sorted(by_day)[-30:]
	chart = {"data": {"labels": [str(d) for d in days],
	                  "datasets": [{"name": "Produced m3",
	                                "values": [round(by_day[d], 2) for d in days]}]},
	         "type": "bar", "colors": ["#16A34A"]}

	total = sum(r[5] for r in data)
	summary = [
		{"label": "Produced m3", "value": round(total, 2), "indicator": "Green"},
		{"label": "Loads", "value": sum(r[3] for r in data), "indicator": "Blue"},
		{"label": "Avg cost / m3",
		 "value": round(sum(r[6] for r in data) / total, 2) if total else 0,
		 "datatype": "Currency", "indicator": "Orange"},
	]
	return columns, data, None, chart, summary

# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Actual batched quantity against the mix design, per material. This is where a drifting load cell or a leaking silo shows up."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	where, params = build_conditions(
		filters, {"plant": "bp.plant", "shift": "bp.shift", "grade": "bp.grade", "item_code": "bm.item_code",
		          "material_type": "bm.material_type"},
		date_field="production_date", alias="bp")

	rows = frappe.db.sql("""
		SELECT bp.production_date, bp.grade, bm.item_code, bm.material_type, bm.uom,
		       SUM(bm.target_qty) target, SUM(bm.actual_qty) actual, SUM(bm.amount) cost
		FROM `tabBatch Material` bm
		JOIN `tabBatch Production` bp ON bp.name = bm.parent
		WHERE bp.docstatus = 1 AND {where}
		GROUP BY bp.production_date, bp.grade, bm.item_code, bm.material_type, bm.uom
		ORDER BY bp.production_date DESC, bp.grade, bm.item_code
	""".format(where=where), params, as_dict=True)

	data = []
	for r in rows:
		var = flt(r.actual) - flt(r.target)
		pct = (100.0 * var / flt(r.target)) if flt(r.target) else 0
		if filters.only_variance and abs(pct) <= 2:
			continue
		data.append([r.production_date, r.grade, r.item_code, r.material_type, r.uom,
		             flt(r.target), flt(r.actual), var, pct, flt(r.cost)])

	columns = [
		col("Date", "Date", 100), col("Grade", "Link", 80, options="Concrete Grade"),
		col("Item", "Link", 180, options="Item"), col("Type", "Data", 100),
		col("UOM", "Data", 70),
		col("Target Qty", "Float", 120, precision=2),
		col("Actual Qty", "Float", 120, precision=2),
		col("Variance", "Float", 110, precision=2),
		col("Variance Pct", "Percent", 115),
		col("Cost", "Currency", 120),
	]

	target = sum(d[5] for d in data)
	actual = sum(d[6] for d in data)
	summary = [
		{"label": "Overall variance",
		 "value": round(100.0 * (actual - target) / target, 2) if target else 0,
		 "datatype": "Percent",
		 "indicator": "Red" if target and abs(actual - target) / target > 0.02 else "Green"},
		{"label": "Material cost", "value": round(sum(d[9] for d in data), 2),
		 "datatype": "Currency", "indicator": "Blue"},
	]
	return columns, data, None, None, summary

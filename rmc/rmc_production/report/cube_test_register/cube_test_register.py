# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Compressive strength achieved against what the grade requires."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	where, params = build_conditions(
		filters, {"batch_production": "ct.batch_production", "grade": "ct.grade", "age_days": "ct.age_days", "result": "ct.result"},
		date_field="casting_date", alias="ct")

	rows = frappe.db.sql("""
		SELECT ct.name, ct.casting_date, ct.testing_date, ct.age_days, ct.grade,
		       ct.batch_production, ct.delivery_challan, ct.no_of_cubes,
		       ct.required_strength_mpa, ct.avg_strength_mpa, ct.strength_pct,
		       ct.result, ct.tested_by
		FROM `tabCube Test` ct
		WHERE ct.docstatus = 1 AND {where}
		ORDER BY ct.casting_date DESC, ct.name DESC
	""".format(where=where), params, as_dict=True)

	data = [[r.name, r.casting_date, r.testing_date, r.age_days, r.grade,
	         r.batch_production, r.delivery_challan, r.no_of_cubes,
	         flt(r.required_strength_mpa), flt(r.avg_strength_mpa),
	         flt(r.strength_pct), r.result, r.tested_by] for r in rows]

	columns = [
		col("Test", "Link", 110, options="Cube Test"),
		col("Cast On", "Date", 95), col("Tested On", "Date", 100),
		col("Age Days", "Data", 75),
		col("Grade", "Link", 75, options="Concrete Grade"),
		col("Batch", "Link", 130, options="Batch Production"),
		col("Challan", "Link", 130, options="Delivery Challan"),
		col("Cubes", "Int", 70),
		col("Required MPa", "Float", 120, precision=1),
		col("Achieved MPa", "Float", 120, precision=1),
		col("Achieved Pct", "Percent", 105),
		col("Result", "Data", 80), col("Tested By", "Data", 130),
	]

	fails = sum(1 for d in data if d[11] == "Fail")
	summary = [
		{"label": "Tests", "value": len(data), "indicator": "Blue"},
		{"label": "Failed", "value": fails,
		 "indicator": "Red" if fails else "Green"},
		{"label": "Pass rate",
		 "value": round(100.0 * (len(data) - fails) / len(data), 1) if data else 0,
		 "datatype": "Percent", "indicator": "Green"},
	]
	return columns, data, None, None, summary

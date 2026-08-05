# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Every batch with its order, customer, operator and the stock entry it posted."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	where, params = build_conditions(
		filters, {"plant": "bp.plant", "grade": "bp.grade", "shift": "bp.shift",
		          "concrete_order": "bp.concrete_order"},
		date_field="production_date", alias="bp")

	rows = frappe.db.sql("""
		SELECT bp.name, bp.production_date, bp.shift, bp.grade, bp.mix_design,
		       bp.qty_m3, bp.no_of_batches, bp.concrete_order, co.customer,
		       bp.operator, bp.cost_per_m3, bp.stock_entry, bp.status
		FROM `tabBatch Production` bp
		LEFT JOIN `tabConcrete Order` co ON co.name = bp.concrete_order
		WHERE bp.docstatus = 1 AND {where}
		ORDER BY bp.production_date DESC, bp.name DESC
	""".format(where=where), params, as_dict=True)

	columns = [
		col("Batch", "Link", 135, options="Batch Production"),
		col("Date", "Date", 95), col("Shift", "Data", 80),
		col("Grade", "Link", 70, options="Concrete Grade"),
		col("Mix Design", "Link", 130, options="Mix Design"),
		col("Qty m3", "Float", 85, precision=2), col("Batches", "Int", 75),
		col("Order", "Link", 120, options="Concrete Order"),
		col("Customer", "Link", 160, options="Customer"),
		col("Operator", "Data", 110), col("Cost per m3", "Currency", 110),
		col("Stock Entry", "Link", 140, options="Stock Entry"),
		col("Status", "Data", 90),
	]
	data = [[r.name, r.production_date, r.shift, r.grade, r.mix_design, flt(r.qty_m3),
	         r.no_of_batches, r.concrete_order, r.customer, r.operator,
	         flt(r.cost_per_m3), r.stock_entry, r.status] for r in rows]

	summary = [
		{"label": "Batches", "value": len(data), "indicator": "Blue"},
		{"label": "Total m3", "value": round(sum(d[5] for d in data), 2),
		 "indicator": "Green"},
	]
	return columns, data, None, None, summary

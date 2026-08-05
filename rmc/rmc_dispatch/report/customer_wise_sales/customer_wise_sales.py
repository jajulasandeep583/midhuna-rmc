# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Value delivered by customer and grade."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	where, params = build_conditions(
		filters, {"customer": "dc.customer", "grade": "dc.grade"},
		date_field="challan_date", alias="dc")

	rows = frappe.db.sql("""
		SELECT dc.customer, dc.grade, COUNT(dc.name) loads, SUM(dc.qty_m3) qty,
		       AVG(dc.rate) rate, SUM(dc.amount) value
		FROM `tabDelivery Challan` dc
		WHERE dc.docstatus = 1 AND {where}
		GROUP BY dc.customer, dc.grade
		ORDER BY SUM(dc.amount) DESC
	""".format(where=where), params, as_dict=True)

	data = [[r.customer, r.grade, r.loads, flt(r.qty), flt(r.rate), flt(r.value)]
	        for r in rows]

	columns = [
		col("Customer", "Link", 190, options="Customer"),
		col("Grade", "Link", 80, options="Concrete Grade"),
		col("Loads", "Int", 80), col("Qty m3", "Float", 110, precision=2),
		col("Avg Rate", "Currency", 120), col("Value", "Currency", 140),
	]

	by_cust = {}
	for d in data:
		by_cust[d[0]] = by_cust.get(d[0], 0) + d[5]
	top = sorted(by_cust.items(), key=lambda kv: -kv[1])[:10]
	chart = {"data": {"labels": [k[:22] for k, _v in top],
	                  "datasets": [{"name": "Value",
	                                "values": [round(v, 0) for _k, v in top]}]},
	         "type": "bar", "colors": ["#047857"]}

	summary = [
		{"label": "Qty m3", "value": round(sum(d[3] for d in data), 2),
		 "indicator": "Green"},
		{"label": "Value", "value": round(sum(d[5] for d in data), 2),
		 "datatype": "Currency", "indicator": "Orange"},
	]
	return columns, data, None, chart, summary

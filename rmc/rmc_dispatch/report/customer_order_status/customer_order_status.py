# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Per customer: what they ordered, took and still owe us a pour for."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	where, params = build_conditions(
		filters, {"grade": "co.grade", "customer": "co.customer", "status": "co.status"},
		date_field="order_date", alias="co")

	rows = frappe.db.sql("""
		SELECT co.customer, COUNT(co.name) orders, SUM(co.order_qty_m3) ordered,
		       SUM(co.delivered_qty_m3) delivered, SUM(co.pending_qty_m3) pending,
		       SUM(co.order_value) value,
		       SUM(CASE WHEN co.status IN ('Open','In Progress') THEN 1 ELSE 0 END) open_orders
		FROM `tabConcrete Order` co
		WHERE co.docstatus = 1 AND {where}
		GROUP BY co.customer
		ORDER BY SUM(co.order_value) DESC
	""".format(where=where), params, as_dict=True)

	data = [[r.customer, r.orders, flt(r.ordered), flt(r.delivered), flt(r.pending),
	         (100.0 * flt(r.delivered) / flt(r.ordered)) if flt(r.ordered) else 0,
	         flt(r.value), r.open_orders] for r in rows]

	columns = [
		col("Customer", "Link", 190, options="Customer"),
		col("Orders", "Int", 80), col("Ordered m3", "Float", 110, precision=2),
		col("Delivered m3", "Float", 115, precision=2),
		col("Pending m3", "Float", 110, precision=2),
		col("Achieved Pct", "Percent", 110),
		col("Order Value", "Currency", 140), col("Open Orders", "Int", 110),
	]

	chart = {"data": {"labels": [d[0][:22] for d in data[:10]],
	                  "datasets": [{"name": "Pending m3",
	                                "values": [round(d[4], 2) for d in data[:10]]}]},
	         "type": "bar", "colors": ["#B45309"]}

	summary = [
		{"label": "Customers", "value": len(data), "indicator": "Blue"},
		{"label": "Pending m3", "value": round(sum(d[4] for d in data), 2),
		 "indicator": "Orange"},
		{"label": "Order value", "value": round(sum(d[6] for d in data), 2),
		 "datatype": "Currency", "indicator": "Green"},
	]
	return columns, data, None, chart, summary

# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Ordered against delivered, order by order."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	where, params = build_conditions(
		filters, {"construction_site": "co.construction_site", "customer": "co.customer", "grade": "co.grade", "status": "co.status"},
		date_field="order_date", alias="co")

	rows = frappe.db.sql("""
		SELECT co.name, co.customer, cs.site_name, co.grade, co.order_qty_m3,
		       co.delivered_qty_m3, co.pending_qty_m3, co.required_from,
		       co.order_value, co.status
		FROM `tabConcrete Order` co
		LEFT JOIN `tabConstruction Site` cs ON cs.name = co.construction_site
		WHERE co.docstatus = 1 AND {where}
		ORDER BY co.required_from DESC
	""".format(where=where), params, as_dict=True)

	data = [[r.name, r.customer, r.site_name, r.grade, flt(r.order_qty_m3),
	         flt(r.delivered_qty_m3), flt(r.pending_qty_m3),
	         (100.0 * flt(r.delivered_qty_m3) / flt(r.order_qty_m3))
	         if flt(r.order_qty_m3) else 0,
	         r.required_from, flt(r.order_value), r.status] for r in rows]

	columns = [
		col("Order", "Link", 125, options="Concrete Order"),
		col("Customer", "Link", 165, options="Customer"),
		col("Site", "Data", 150), col("Grade", "Link", 70, options="Concrete Grade"),
		col("Ordered m3", "Float", 105, precision=2),
		col("Delivered m3", "Float", 115, precision=2),
		col("Pending m3", "Float", 105, precision=2),
		col("Achieved Pct", "Percent", 105),
		col("Required From", "Date", 115),
		col("Order Value", "Currency", 130), col("Status", "Data", 100),
	]

	ordered = sum(d[4] for d in data)
	delivered = sum(d[5] for d in data)
	summary = [
		{"label": "Ordered m3", "value": round(ordered, 2), "indicator": "Blue"},
		{"label": "Delivered m3", "value": round(delivered, 2), "indicator": "Green"},
		{"label": "Pending m3", "value": round(ordered - delivered, 2),
		 "indicator": "Orange"},
	]
	return columns, data, None, None, summary

# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Every rupee billed, straight off the invoices the challans raised — the register you reconcile with accounts."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	conds, params = ["si.docstatus = 1"], {}
	if filters.get("from_date"):
		conds.append("si.posting_date >= %(from_date)s")
		params["from_date"] = filters.from_date
	if filters.get("to_date"):
		conds.append("si.posting_date <= %(to_date)s")
		params["to_date"] = filters.to_date
	if filters.get("customer"):
		conds.append("si.customer = %(customer)s")
		params["customer"] = filters.customer
	if filters.get("status"):
		conds.append("si.status = %(status)s")
		params["status"] = filters.status
	if filters.get("grade"):
		conds.append("dc.grade = %(grade)s")
		params["grade"] = filters.grade
	where = " AND ".join(conds)

	rows = frappe.db.sql("""
		SELECT si.name, si.posting_date, si.customer, dc.grade, sii.qty, sii.rate,
		       si.net_total, si.grand_total, si.outstanding_amount, si.status,
		       si.rmc_delivery_challan challan, cs.site_name
		FROM `tabSales Invoice` si
		JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
		LEFT JOIN `tabDelivery Challan` dc ON dc.name = si.rmc_delivery_challan
		LEFT JOIN `tabConstruction Site` cs ON cs.name = si.rmc_construction_site
		WHERE {where}
		ORDER BY si.posting_date DESC, si.name DESC
	""".format(where=where), params, as_dict=True)

	data = [[r.name, r.posting_date, r.customer, r.site_name, r.grade, flt(r.qty),
	         flt(r.rate), flt(r.net_total), flt(r.grand_total),
	         flt(r.outstanding_amount), r.status, r.challan] for r in rows]

	columns = [
		col("Invoice", "Link", 145, options="Sales Invoice"),
		col("Date", "Date", 95), col("Customer", "Link", 175, options="Customer"),
		col("Site", "Data", 150), col("Grade", "Link", 70, options="Concrete Grade"),
		col("Qty m3", "Float", 85, precision=2), col("Rate", "Currency", 100),
		col("Net Total", "Currency", 125), col("Grand Total", "Currency", 130),
		col("Outstanding", "Currency", 125), col("Status", "Data", 95),
		col("Challan", "Link", 135, options="Delivery Challan"),
	]

	by_day = {}
	for d in data:
		by_day[d[1]] = by_day.get(d[1], 0) + d[8]
	days = sorted(by_day)[-30:]
	chart = {"data": {"labels": [str(x) for x in days],
	                  "datasets": [{"name": "Billed",
	                                "values": [round(by_day[x], 0) for x in days]}]},
	         "type": "line", "colors": ["#047857"]}

	summary = [
		{"label": "Invoices", "value": len(data), "indicator": "Blue"},
		{"label": "Billed", "value": round(sum(d[8] for d in data), 2),
		 "datatype": "Currency", "indicator": "Green"},
		{"label": "Outstanding", "value": round(sum(d[9] for d in data), 2),
		 "datatype": "Currency", "indicator": "Red"},
		{"label": "Qty m3", "value": round(sum(d[5] for d in data), 2),
		 "indicator": "Purple"},
	]
	return columns, data, None, chart, summary

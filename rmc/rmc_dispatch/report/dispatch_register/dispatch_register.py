# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Every load that left the plant, with its trip times and invoice."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	where, params = build_conditions(
		filters, {"construction_site": "dc.construction_site", "driver": "dc.driver", "customer": "dc.customer", "grade": "dc.grade",
		          "transit_mixer": "dc.transit_mixer", "status": "dc.status"},
		date_field="challan_date", alias="dc")

	rows = frappe.db.sql("""
		SELECT dc.name, dc.challan_date, dc.customer, cs.site_name, dc.grade,
		       dc.qty_m3, dc.rate, dc.amount, dc.transit_mixer, dc.driver_name,
		       dc.dispatch_time, dc.cycle_time_min, dc.slump_mm, dc.status,
		       dc.sales_invoice
		FROM `tabDelivery Challan` dc
		LEFT JOIN `tabConstruction Site` cs ON cs.name = dc.construction_site
		WHERE dc.docstatus = 1 AND {where}
		ORDER BY dc.challan_date DESC, dc.dispatch_time DESC
	""".format(where=where), params, as_dict=True)

	data = [[r.name, r.challan_date, r.customer, r.site_name, r.grade, flt(r.qty_m3),
	         flt(r.rate), flt(r.amount), r.transit_mixer, r.driver_name,
	         r.dispatch_time, r.cycle_time_min, r.slump_mm, r.status,
	         r.sales_invoice] for r in rows]

	columns = [
		col("Challan", "Link", 130, options="Delivery Challan"),
		col("Date", "Date", 95), col("Customer", "Link", 160, options="Customer"),
		col("Site", "Data", 150), col("Grade", "Link", 70, options="Concrete Grade"),
		col("Qty m3", "Float", 85, precision=2), col("Rate", "Currency", 95),
		col("Amount", "Currency", 120),
		col("Vehicle", "Link", 115, options="Transit Mixer"),
		col("Driver", "Data", 130), col("Dispatch", "Datetime", 145),
		col("Cycle Min", "Int", 95), col("Slump", "Int", 70),
		col("Status", "Data", 95),
		col("Invoice", "Link", 140, options="Sales Invoice"),
	]

	by_day = {}
	for d in data:
		by_day[d[1]] = by_day.get(d[1], 0) + d[5]
	days = sorted(by_day)[-30:]
	chart = {"data": {"labels": [str(x) for x in days],
	                  "datasets": [{"name": "Dispatched m3",
	                                "values": [round(by_day[x], 2) for x in days]}]},
	         "type": "line", "colors": ["#9333EA"]}

	cycles = [d[11] for d in data if d[11]]
	summary = [
		{"label": "Loads", "value": len(data), "indicator": "Blue"},
		{"label": "Dispatched m3", "value": round(sum(d[5] for d in data), 2),
		 "indicator": "Green"},
		{"label": "Value", "value": round(sum(d[7] for d in data), 2),
		 "datatype": "Currency", "indicator": "Orange"},
		{"label": "Avg cycle min",
		 "value": round(sum(cycles) / len(cycles), 1) if cycles else 0,
		 "indicator": "Purple"},
	]
	return columns, data, None, chart, summary

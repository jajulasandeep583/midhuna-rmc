# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""What is promised and when — every scheduled pour still owed to a customer."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	conds, params = [], {}
	if filters.get("from_date"):
		conds.append("os.schedule_date >= %(from_date)s")
		params["from_date"] = filters.from_date
	if filters.get("to_date"):
		conds.append("os.schedule_date <= %(to_date)s")
		params["to_date"] = filters.to_date
	for key, column in (("customer", "co.customer"), ("grade", "co.grade")):
		if filters.get(key):
			conds.append("%s = %%(%s)s" % (column, key))
			params[key] = filters.get(key)
	where = " AND ".join(conds) or "1=1"

	rows = frappe.db.sql("""
		SELECT os.schedule_date, os.time_slot, os.qty_m3, co.name, co.customer,
		       cs.site_name, co.grade, co.rate, co.status, co.delivered_qty_m3,
		       co.order_qty_m3, cs.distance_km, co.pump_required
		FROM `tabOrder Schedule` os
		JOIN `tabConcrete Order` co ON co.name = os.parent
		LEFT JOIN `tabConstruction Site` cs ON cs.name = co.construction_site
		WHERE co.docstatus = 1 AND {where}
		ORDER BY os.schedule_date, co.customer
	""".format(where=where), params, as_dict=True)

	data = []
	for r in rows:
		delivered = flt(frappe.db.sql("""
			SELECT SUM(qty_m3) FROM `tabDelivery Challan`
			WHERE docstatus = 1 AND concrete_order = %s AND challan_date = %s""",
			(r.name, r.schedule_date))[0][0])
		pending = flt(r.qty_m3) - delivered
		if filters.only_variance if False else (filters.only_pending and pending <= 0.001):
			continue
		data.append([r.schedule_date, r.time_slot, r.name, r.customer, r.site_name,
		             r.grade, flt(r.qty_m3), delivered, pending,
		             flt(r.qty_m3) * flt(r.rate), flt(r.distance_km),
		             "Yes" if r.pump_required else "No", r.status])

	columns = [
		col("Pour Date", "Date", 100), col("Time Slot", "Data", 110),
		col("Order", "Link", 120, options="Concrete Order"),
		col("Customer", "Link", 165, options="Customer"),
		col("Site", "Data", 150), col("Grade", "Link", 70, options="Concrete Grade"),
		col("Scheduled m3", "Float", 115, precision=2),
		col("Delivered m3", "Float", 115, precision=2),
		col("Pending m3", "Float", 110, precision=2),
		col("Value", "Currency", 125), col("Distance km", "Float", 105, precision=1),
		col("Pump", "Data", 70), col("Status", "Data", 100),
	]

	by_day = {}
	for d in data:
		by_day[d[0]] = by_day.get(d[0], 0) + d[8]
	days = sorted(by_day)[:30]
	chart = {"data": {"labels": [str(x) for x in days],
	                  "datasets": [{"name": "Pending m3",
	                                "values": [round(by_day[x], 2) for x in days]}]},
	         "type": "bar", "colors": ["#B45309"]}

	summary = [
		{"label": "Scheduled pours", "value": len(data), "indicator": "Blue"},
		{"label": "Pending m3", "value": round(sum(d[8] for d in data), 2),
		 "indicator": "Orange"},
		{"label": "Order value", "value": round(sum(d[9] for d in data), 2),
		 "datatype": "Currency", "indicator": "Green"},
	]
	return columns, data, None, chart, summary

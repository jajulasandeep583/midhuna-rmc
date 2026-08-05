# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Trips, load factor and cycle time for every transit mixer."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	where, params = build_conditions(
		filters, {"transit_mixer": "dc.transit_mixer", "vehicle_type": "tm.vehicle_type"},
		date_field="challan_date", alias="dc")

	rows = frappe.db.sql("""
		SELECT dc.transit_mixer, tm.vehicle_type, tm.capacity_m3, tm.ownership,
		       COUNT(dc.name) trips, SUM(dc.qty_m3) qty, AVG(dc.cycle_time_min) cycle,
		       SUM(dc.distance_km) km, SUM(dc.amount) revenue
		FROM `tabDelivery Challan` dc
		LEFT JOIN `tabTransit Mixer` tm ON tm.name = dc.transit_mixer
		WHERE dc.docstatus = 1 AND {where}
		GROUP BY dc.transit_mixer, tm.vehicle_type, tm.capacity_m3, tm.ownership
		ORDER BY COUNT(dc.name) DESC
	""".format(where=where), params, as_dict=True)

	data = []
	for r in rows:
		avg_load = flt(r.qty) / r.trips if r.trips else 0
		util = (100.0 * avg_load / flt(r.capacity_m3)) if flt(r.capacity_m3) else 0
		data.append([r.transit_mixer, r.vehicle_type, r.ownership, flt(r.capacity_m3),
		             r.trips, flt(r.qty), avg_load, util, flt(r.cycle), flt(r.km),
		             flt(r.revenue)])

	columns = [
		col("Vehicle", "Link", 125, options="Transit Mixer"),
		col("Type", "Data", 120), col("Ownership", "Data", 95),
		col("Capacity m3", "Float", 110, precision=1),
		col("Trips", "Int", 80), col("Delivered m3", "Float", 120, precision=2),
		col("Avg Load m3", "Float", 115, precision=2),
		col("Load Factor", "Percent", 110),
		col("Avg Cycle Min", "Float", 125, precision=1),
		col("Distance km", "Float", 110, precision=1),
		col("Revenue Carried", "Currency", 150),
	]

	chart = {"data": {"labels": [d[0] for d in data],
	                  "datasets": [{"name": "Trips", "values": [d[4] for d in data]}]},
	         "type": "bar", "colors": ["#2563EB"]}

	summary = [
		{"label": "Trips", "value": sum(d[4] for d in data), "indicator": "Blue"},
		{"label": "Avg cycle min",
		 "value": round(sum(d[8] for d in data) / len(data), 1) if data else 0,
		 "indicator": "Purple"},
		{"label": "Avg load factor",
		 "value": round(sum(d[7] for d in data) / len(data), 1) if data else 0,
		 "datatype": "Percent", "indicator": "Green"},
	]
	return columns, data, None, chart, summary

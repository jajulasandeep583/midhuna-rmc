# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Trips, quantity carried and cycle time by driver."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	where, params = build_conditions(
		filters, {"driver": "dc.driver", "transit_mixer": "dc.transit_mixer"},
		date_field="challan_date", alias="dc")

	rows = frappe.db.sql("""
		SELECT dc.driver, dc.driver_name, COUNT(dc.name) trips, SUM(dc.qty_m3) qty,
		       AVG(dc.cycle_time_min) cycle, MIN(dc.cycle_time_min) best,
		       MAX(dc.cycle_time_min) worst, SUM(dc.distance_km) km,
		       COUNT(DISTINCT dc.challan_date) days, SUM(dc.amount) value
		FROM `tabDelivery Challan` dc
		WHERE dc.docstatus = 1 AND dc.driver IS NOT NULL AND {where}
		GROUP BY dc.driver, dc.driver_name
		ORDER BY COUNT(dc.name) DESC
	""".format(where=where), params, as_dict=True)

	data = [[r.driver, r.driver_name, r.trips, r.days,
	         round(r.trips / r.days, 2) if r.days else 0, flt(r.qty), flt(r.cycle),
	         r.best, r.worst, flt(r.km), flt(r.value)] for r in rows]

	columns = [
		col("Driver", "Link", 130, options="Driver"), col("Name", "Data", 150),
		col("Trips", "Int", 80), col("Days Worked", "Int", 110),
		col("Trips per Day", "Float", 120, precision=2),
		col("Delivered m3", "Float", 120, precision=2),
		col("Avg Cycle Min", "Float", 125, precision=1),
		col("Best Min", "Int", 95), col("Worst Min", "Int", 100),
		col("Distance km", "Float", 110, precision=1),
		col("Value Carried", "Currency", 140),
	]

	chart = {"data": {"labels": [d[1] or d[0] for d in data],
	                  "datasets": [{"name": "Trips", "values": [d[2] for d in data]}]},
	         "type": "bar", "colors": ["#0369A1"]}

	summary = [
		{"label": "Drivers", "value": len(data), "indicator": "Blue"},
		{"label": "Trips", "value": sum(d[2] for d in data), "indicator": "Green"},
		{"label": "Avg cycle min",
		 "value": round(sum(d[6] for d in data) / len(data), 1) if data else 0,
		 "indicator": "Purple"},
	]
	return columns, data, None, chart, summary

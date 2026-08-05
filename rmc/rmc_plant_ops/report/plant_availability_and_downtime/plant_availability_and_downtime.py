# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Running, idle and breakdown hours per day, and the availability they imply."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	where, params = build_conditions(
		filters, {"plant": "psl.plant", "shift": "psl.shift"},
		date_field="log_date", alias="psl")

	rows = frappe.db.sql("""
		SELECT psl.log_date, psl.plant,
		       SUM(CASE WHEN psl.status='Running' THEN psl.duration_hours ELSE 0 END) running,
		       SUM(CASE WHEN psl.status='Idle' THEN psl.duration_hours ELSE 0 END) idle,
		       SUM(CASE WHEN psl.status='Breakdown' THEN psl.duration_hours ELSE 0 END) breakdown,
		       SUM(CASE WHEN psl.status='Stopped' THEN psl.duration_hours ELSE 0 END) stopped,
		       SUM(psl.duration_hours) logged
		FROM `tabPlant Status Log` psl
		WHERE {where}
		GROUP BY psl.log_date, psl.plant
		ORDER BY psl.log_date DESC
	""".format(where=where), params, as_dict=True)

	data = []
	for r in rows:
		up = flt(r.running) + flt(r.idle)
		avail = (100.0 * up / flt(r.logged)) if flt(r.logged) else 0
		util = (100.0 * flt(r.running) / flt(r.logged)) if flt(r.logged) else 0
		data.append([r.log_date, r.plant, flt(r.running), flt(r.idle),
		             flt(r.breakdown), flt(r.stopped), flt(r.logged), avail, util])

	columns = [
		col("Date", "Date", 100), col("Plant", "Link", 210, options="RMC Plant"),
		col("Running Hrs", "Float", 110, precision=2),
		col("Idle Hrs", "Float", 95, precision=2),
		col("Breakdown Hrs", "Float", 125, precision=2),
		col("Stopped Hrs", "Float", 110, precision=2),
		col("Logged Hrs", "Float", 105, precision=2),
		col("Availability Pct", "Percent", 125),
		col("Utilisation Pct", "Percent", 120),
	]

	days = [d[0] for d in data][::-1][-30:]
	avails = [round(d[7], 1) for d in data][::-1][-30:]
	chart = {"data": {"labels": [str(x) for x in days],
	                  "datasets": [{"name": "Availability %", "values": avails}]},
	         "type": "line", "colors": ["#2DD4BF"]}

	logged = sum(d[6] for d in data)
	up = sum(d[2] + d[3] for d in data)
	summary = [
		{"label": "Availability",
		 "value": round(100.0 * up / logged, 1) if logged else 0,
		 "datatype": "Percent", "indicator": "Green"},
		{"label": "Breakdown hrs", "value": round(sum(d[4] for d in data), 2),
		 "indicator": "Red"},
		{"label": "Running hrs", "value": round(sum(d[2] for d in data), 2),
		 "indicator": "Blue"},
	]
	return columns, data, None, chart, summary

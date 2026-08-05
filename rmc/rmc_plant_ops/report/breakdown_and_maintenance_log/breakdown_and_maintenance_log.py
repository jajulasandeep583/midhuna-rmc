# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Every stoppage, how long it lasted and what it cost to put right."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	conds, params = [], {}
	if filters.get("from_date"):
		conds.append("DATE(bd.reported_on) >= %(from_date)s")
		params["from_date"] = filters.from_date
	if filters.get("to_date"):
		conds.append("DATE(bd.reported_on) <= %(to_date)s")
		params["to_date"] = filters.to_date
	for key, column in (("plant", "bd.plant"), ("equipment", "bd.equipment"),
	                    ("status", "bd.status"), ("severity", "bd.severity")):
		if filters.get(key):
			conds.append("%s = %%(%s)s" % (column, key))
			params[key] = filters.get(key)
	where = " AND ".join(conds) or "1=1"

	rows = frappe.db.sql("""
		SELECT bd.name, bd.plant, bd.equipment, bd.transit_mixer, bd.reported_on,
		       bd.resolved_on, bd.downtime_hours, bd.severity, bd.status,
		       bd.reason, bd.action_taken, bd.attended_by, bd.spare_cost
		FROM `tabBreakdown Log` bd
		WHERE {where}
		ORDER BY bd.reported_on DESC
	""".format(where=where), params, as_dict=True)

	data = [[r.name, r.plant, r.equipment, r.transit_mixer, r.reported_on,
	         r.resolved_on, flt(r.downtime_hours), r.severity, r.status, r.reason,
	         r.action_taken, r.attended_by, flt(r.spare_cost)] for r in rows]

	columns = [
		col("Breakdown", "Link", 120, options="Breakdown Log"),
		col("Plant", "Link", 190, options="RMC Plant"),
		col("Equipment", "Data", 140),
		col("Transit Mixer", "Link", 120, options="Transit Mixer"),
		col("Reported", "Datetime", 150), col("Resolved", "Datetime", 150),
		col("Downtime Hrs", "Float", 120, precision=2),
		col("Severity", "Data", 90), col("Status", "Data", 90),
		col("Reason", "Data", 240), col("Action Taken", "Data", 240),
		col("Attended By", "Data", 130), col("Repair Cost", "Currency", 120),
	]

	by_equip = {}
	for d in data:
		by_equip[d[2]] = by_equip.get(d[2], 0) + d[6]
	chart = {"data": {"labels": list(by_equip),
	                  "datasets": [{"name": "Downtime hrs",
	                                "values": [round(v, 2) for v in by_equip.values()]}]},
	         "type": "bar", "colors": ["#E11D48"]}

	open_n = sum(1 for d in data if d[8] != "Closed")
	summary = [
		{"label": "Breakdowns", "value": len(data), "indicator": "Blue"},
		{"label": "Downtime hrs", "value": round(sum(d[6] for d in data), 2),
		 "indicator": "Red"},
		{"label": "Still open", "value": open_n,
		 "indicator": "Red" if open_n else "Green"},
		{"label": "Repair cost", "value": round(sum(d[12] for d in data), 2),
		 "datatype": "Currency", "indicator": "Orange"},
	]
	return columns, data, None, chart, summary

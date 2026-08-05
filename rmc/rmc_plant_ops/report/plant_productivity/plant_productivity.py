# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Output against the hours the plant actually ran — m³ per running hour, per shift and per operator, and what that is of rated capacity."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	group_by = filters.group_by or "Date"
	where, params = build_conditions(
		filters, {"plant": "bp.plant", "shift": "bp.shift"},
		date_field="production_date", alias="bp")

	dim = {"Date": "bp.production_date", "Shift": "bp.shift",
	       "Operator": "bp.operator", "Grade": "bp.grade"}[group_by]

	rows = frappe.db.sql("""
		SELECT {dim} dim, COUNT(bp.name) loads, SUM(bp.no_of_batches) batches,
		       SUM(bp.qty_m3) qty, SUM(bp.total_material_cost) cost,
		       COUNT(DISTINCT bp.production_date) days
		FROM `tabBatch Production` bp
		WHERE bp.docstatus = 1 AND {where}
		GROUP BY {dim} ORDER BY {dim}
	""".format(dim=dim, where=where), params, as_dict=True)

	# running hours from the status log, keyed the same way where it can be
	hours = {}
	if group_by in ("Date", "Shift"):
		hcol = "psl.log_date" if group_by == "Date" else "psl.shift"
		hwhere, hparams = build_conditions(
			filters, {"plant": "psl.plant", "shift": "psl.shift"},
			date_field="log_date", alias="psl")
		for r in frappe.db.sql("""
			SELECT {hcol} dim,
			       SUM(CASE WHEN psl.status = 'Running' THEN psl.duration_hours ELSE 0 END) run,
			       SUM(psl.duration_hours) logged
			FROM `tabPlant Status Log` psl WHERE {hwhere} GROUP BY {hcol}
		""".format(hcol=hcol, hwhere=hwhere), hparams, as_dict=True):
			hours[str(r.dim)] = r

	capacity = flt(frappe.db.get_value(
		"RMC Plant", filters.plant or frappe.db.get_single_value(
			"RMC Settings", "default_plant"), "capacity_m3_hr")) or 60

	data = []
	for r in rows:
		h = hours.get(str(r.dim))
		run = flt(h.run) if h else 0
		logged = flt(h.logged) if h else 0
		per_hour = (flt(r.qty) / run) if run else 0
		data.append([
			r.dim, r.days, r.loads, r.batches, flt(r.qty),
			flt(r.qty) / r.days if r.days else 0,
			run, per_hour,
			(100.0 * per_hour / capacity) if capacity else 0,
			(100.0 * run / logged) if logged else 0,
			flt(r.cost) / flt(r.qty) if flt(r.qty) else 0,
		])

	columns = [
		col(group_by, "Data", 130), col("Days", "Int", 70),
		col("Loads", "Int", 75), col("Batches", "Int", 85),
		col("Produced m3", "Float", 115, precision=2),
		col("m3 per Day", "Float", 110, precision=2),
		col("Running Hrs", "Float", 110, precision=2),
		col("m3 per Hour", "Float", 115, precision=2),
		col("Of Capacity Pct", "Percent", 125),
		col("Utilisation Pct", "Percent", 120),
		col("Cost per m3", "Currency", 115),
	]

	chart = {"data": {"labels": [str(d[0]) for d in data][-30:],
	                  "datasets": [{"name": "m3 per hour",
	                                "values": [round(d[7], 2) for d in data][-30:]}]},
	         "type": "line", "colors": ["#0F766E"]}

	qty = sum(d[4] for d in data)
	run = sum(d[6] for d in data)
	summary = [
		{"label": "Produced m3", "value": round(qty, 2), "indicator": "Green"},
		{"label": "m3 per running hour", "value": round(qty / run, 2) if run else 0,
		 "indicator": "Blue"},
		{"label": "Of rated capacity",
		 "value": round(100.0 * (qty / run) / capacity, 1) if run and capacity else 0,
		 "datatype": "Percent", "indicator": "Orange"},
	]
	return columns, data, None, chart, summary

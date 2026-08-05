# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""EB and DG units, diesel burnt, and what each unit of concrete cost in power."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	where, params = build_conditions(
		filters, {"plant": "pl.plant"}, date_field="log_date", alias="pl")

	rows = frappe.db.sql("""
		SELECT pl.log_date, pl.plant, pl.eb_units, pl.eb_hours, pl.dg_units,
		       pl.dg_hours, pl.diesel_litres, pl.diesel_cost
		FROM `tabPower Log` pl
		WHERE {where}
		ORDER BY pl.log_date DESC
	""".format(where=where), params, as_dict=True)

	produced = dict(frappe.db.sql("""
		SELECT production_date, SUM(qty_m3) FROM `tabBatch Production`
		WHERE docstatus = 1 GROUP BY production_date"""))

	data = []
	for r in rows:
		total_units = flt(r.eb_units) + flt(r.dg_units)
		m3 = flt(produced.get(r.log_date, 0))
		data.append([r.log_date, r.plant, flt(r.eb_units), flt(r.eb_hours),
		             flt(r.dg_units), flt(r.dg_hours), flt(r.diesel_litres),
		             flt(r.diesel_cost), total_units, m3,
		             (total_units / m3) if m3 else 0])

	columns = [
		col("Date", "Date", 100), col("Plant", "Link", 200, options="RMC Plant"),
		col("EB Units", "Float", 100, precision=1),
		col("EB Hrs", "Float", 90, precision=1),
		col("DG Units", "Float", 100, precision=1),
		col("DG Hrs", "Float", 90, precision=1),
		col("Diesel L", "Float", 100, precision=1),
		col("Diesel Cost", "Currency", 120),
		col("Total Units", "Float", 110, precision=1),
		col("Produced m3", "Float", 110, precision=2),
		col("Units per m3", "Float", 115, precision=2),
	]

	days = [d[0] for d in data][::-1][-30:]
	chart = {"data": {"labels": [str(x) for x in days],
	                  "datasets": [
	                      {"name": "EB units",
	                       "values": [round(d[2], 1) for d in data][::-1][-30:]},
	                      {"name": "DG units",
	                       "values": [round(d[4], 1) for d in data][::-1][-30:]}]},
	         "type": "bar", "colors": ["#EAB308", "#B91C1C"]}

	units = sum(d[8] for d in data)
	m3 = sum(d[9] for d in data)
	summary = [
		{"label": "Total units", "value": round(units, 1), "indicator": "Blue"},
		{"label": "Diesel L", "value": round(sum(d[6] for d in data), 1),
		 "indicator": "Red"},
		{"label": "Units per m3", "value": round(units / m3, 2) if m3 else 0,
		 "indicator": "Orange"},
	]
	return columns, data, None, chart, summary

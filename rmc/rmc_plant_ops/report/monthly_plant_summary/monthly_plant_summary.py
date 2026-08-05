# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""One line per month: produced, dispatched, purchased, availability and margin."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	f = {"from_date": filters.get("from_date"), "to_date": filters.get("to_date"),
	     "plant": filters.get("plant")}
	pc = " AND plant = %(plant)s" if filters.get("plant") else ""

	prod = {r.m: r for r in frappe.db.sql("""
		SELECT DATE_FORMAT(production_date, '%%Y-%%m') m, COUNT(name) batches,
		       SUM(qty_m3) qty, SUM(total_material_cost) cost
		FROM `tabBatch Production`
		WHERE docstatus = 1 AND production_date BETWEEN %(from_date)s AND %(to_date)s
		""" + pc + """ GROUP BY m""", f, as_dict=True)}
	disp = {r.m: r for r in frappe.db.sql("""
		SELECT DATE_FORMAT(challan_date, '%%Y-%%m') m, COUNT(name) loads,
		       SUM(qty_m3) qty, SUM(amount) value
		FROM `tabDelivery Challan`
		WHERE docstatus = 1 AND challan_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY m""", f, as_dict=True)}
	buy = {r.m: r for r in frappe.db.sql("""
		SELECT DATE_FORMAT(inward_date, '%%Y-%%m') m, SUM(net_weight) mt, SUM(amount) value
		FROM `tabMaterial Inward`
		WHERE docstatus = 1 AND inward_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY m""", f, as_dict=True)}
	avail = {r.m: r for r in frappe.db.sql("""
		SELECT DATE_FORMAT(log_date, '%%Y-%%m') m,
		       SUM(CASE WHEN status IN ('Running','Idle') THEN duration_hours ELSE 0 END) up,
		       SUM(duration_hours) total,
		       SUM(CASE WHEN status = 'Breakdown' THEN duration_hours ELSE 0 END) bd
		FROM `tabPlant Status Log`
		WHERE log_date BETWEEN %(from_date)s AND %(to_date)s
		""" + pc + """ GROUP BY m""", f, as_dict=True)}

	months = sorted(set(list(prod) + list(disp) + list(buy) + list(avail)), reverse=True)
	data = []
	for m in months:
		p, d, b, a = prod.get(m), disp.get(m), buy.get(m), avail.get(m)
		revenue = flt(d.value) if d else 0
		cost = flt(p.cost) if p else 0
		data.append([
			m, (p.batches if p else 0), flt(p.qty) if p else 0,
			(d.loads if d else 0), flt(d.qty) if d else 0, revenue,
			flt(b.mt) if b else 0, flt(b.value) if b else 0,
			cost, revenue - cost,
			(100.0 * (revenue - cost) / revenue) if revenue else 0,
			(100.0 * flt(a.up) / flt(a.total)) if a and flt(a.total) else 0,
			flt(a.bd) if a else 0,
		])

	columns = [
		col("Month", "Data", 90), col("Batches", "Int", 85),
		col("Produced m3", "Float", 115, precision=2), col("Loads", "Int", 80),
		col("Dispatched m3", "Float", 120, precision=2),
		col("Revenue", "Currency", 130), col("Bought MT", "Float", 105, precision=2),
		col("Purchase Value", "Currency", 135), col("Material Cost", "Currency", 130),
		col("Gross Margin", "Currency", 130), col("Margin Pct", "Percent", 105),
		col("Availability Pct", "Percent", 120),
		col("Breakdown Hrs", "Float", 120, precision=2),
	]

	chart = {"data": {"labels": [d[0] for d in data][::-1],
	                  "datasets": [
	                      {"name": "Produced m3", "values": [round(d[2], 1) for d in data][::-1]},
	                      {"name": "Dispatched m3", "values": [round(d[4], 1) for d in data][::-1]}]},
	         "type": "bar", "colors": ["#16A34A", "#9333EA"]}

	rev = sum(d[5] for d in data)
	summary = [
		{"label": "Months", "value": len(data), "indicator": "Blue"},
		{"label": "Revenue", "value": round(rev, 2), "datatype": "Currency",
		 "indicator": "Green"},
		{"label": "Gross margin", "value": round(sum(d[9] for d in data), 2),
		 "datatype": "Currency", "indicator": "Orange"},
	]
	return columns, data, None, chart, summary

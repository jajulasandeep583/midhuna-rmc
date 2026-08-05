# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Slump measured at site against the target the mix design was written for."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


TOLERANCE = 25          # mm either side of the design target, the usual site allowance


def execute(filters=None):
	filters = frappe._dict(filters or {})
	where, params = build_conditions(
		filters, {"grade": "dc.grade", "customer": "dc.customer"},
		date_field="challan_date", alias="dc")

	rows = frappe.db.sql("""
		SELECT dc.name, dc.challan_date, dc.customer, dc.grade, dc.qty_m3, dc.slump_mm,
		       dc.temperature_c, dc.transit_mixer, dc.cycle_time_min,
		       md.slump_target_mm target
		FROM `tabDelivery Challan` dc
		LEFT JOIN `tabMix Design` md ON md.grade = dc.grade AND md.is_active = 1
		WHERE dc.docstatus = 1 AND IFNULL(dc.slump_mm, 0) > 0 AND {where}
		ORDER BY dc.challan_date DESC
	""".format(where=where), params, as_dict=True)

	data = []
	for r in rows:
		target = flt(r.target) or 100
		dev = flt(r.slump_mm) - target
		ok = abs(dev) <= TOLERANCE
		if filters.only_out and ok:
			continue
		data.append([r.name, r.challan_date, r.customer, r.grade, flt(r.qty_m3),
		             target, r.slump_mm, dev, "Within" if ok else "Outside",
		             flt(r.temperature_c), r.transit_mixer, r.cycle_time_min])

	columns = [
		col("Challan", "Link", 130, options="Delivery Challan"),
		col("Date", "Date", 95), col("Customer", "Link", 160, options="Customer"),
		col("Grade", "Link", 70, options="Concrete Grade"),
		col("Qty m3", "Float", 85, precision=2),
		col("Target mm", "Int", 100), col("Measured mm", "Int", 110),
		col("Deviation mm", "Int", 115), col("Result", "Data", 90),
		col("Temp C", "Float", 85, precision=1),
		col("Vehicle", "Link", 115, options="Transit Mixer"),
		col("Cycle Min", "Int", 95),
	]

	buckets = {}
	for d in data:
		buckets[d[6]] = buckets.get(d[6], 0) + 1
	keys = sorted(buckets)
	chart = {"data": {"labels": [str(k) for k in keys],
	                  "datasets": [{"name": "Loads", "values": [buckets[k] for k in keys]}]},
	         "type": "bar", "colors": ["#F59E0B"]}

	out = sum(1 for d in data if d[8] == "Outside")
	summary = [
		{"label": "Loads measured", "value": len(data), "indicator": "Blue"},
		{"label": "Outside tolerance", "value": out,
		 "indicator": "Red" if out else "Green"},
		{"label": "Compliance",
		 "value": round(100.0 * (len(data) - out) / len(data), 1) if data else 0,
		 "datatype": "Percent", "indicator": "Green"},
	]
	return columns, data, None, chart, summary

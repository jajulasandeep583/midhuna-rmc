# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Live level of every silo and yard, against capacity and the alert level."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	conds = {"material_type": "s.material_type"}
	where, params = build_conditions(filters, conds)

	rows = frappe.db.sql("""
		SELECT s.name, s.silo_name, s.material_type, s.item_code, s.capacity_mt,
		       s.min_level_mt, s.warehouse,
		       IFNULL(b.actual_qty, 0) qty, IFNULL(b.stock_value, 0) value
		FROM `tabSilo` s
		LEFT JOIN `tabBin` b ON b.warehouse = s.warehouse AND b.item_code = s.item_code
		WHERE s.is_active = 1 AND {where}
		ORDER BY s.material_type, s.silo_name
	""".format(where=where), params, as_dict=True)

	data = []
	for r in rows:
		stock = flt(r.qty) / 1000.0
		pct = (100.0 * stock / flt(r.capacity_mt)) if flt(r.capacity_mt) else 0
		low = bool(r.min_level_mt and stock <= flt(r.min_level_mt))
		if filters.only_low and not low:
			continue
		data.append([r.name, r.material_type, r.item_code, flt(r.capacity_mt), stock,
		             pct, flt(r.min_level_mt), "LOW - REORDER" if low else "OK",
		             flt(r.value), r.warehouse])

	columns = [
		col("Silo", "Link", 170, options="Silo"), col("Material", "Data", 110),
		col("Item", "Link", 175, options="Item"),
		col("Capacity", "Float", 100, precision=2),
		col("Stock", "Float", 110, precision=2),
		col("Filled Pct", "Percent", 100),
		col("Low Level", "Float", 100, precision=2),
		col("Alert", "Data", 130), col("Stock Value", "Currency", 130),
		col("Warehouse", "Link", 180, options="Warehouse"),
	]

	chart = {"data": {"labels": [d[0] for d in data],
	                  "datasets": [{"name": "Filled %", "values":
	                                [round(d[5], 1) for d in data]}]},
	         "type": "bar", "colors": ["#0F766E"]}

	lows = sum(1 for d in data if d[7].startswith("LOW"))
	summary = [
		{"label": "Silos", "value": len(data), "indicator": "Blue"},
		{"label": "Below alert level", "value": lows,
		 "indicator": "Red" if lows else "Green"},
		{"label": "Stock value", "value": round(sum(d[8] for d in data), 2),
		 "datatype": "Currency", "indicator": "Orange"},
	]
	return columns, data, None, chart, summary

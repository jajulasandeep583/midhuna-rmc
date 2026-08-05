# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""What the plant burnt, bought and still holds, material by material — the one page a purchase manager needs before ordering."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	cwhere, cparams = build_conditions(
		filters, {"material_type": "bm.material_type", "plant": "bp.plant"},
		date_field="production_date", alias="bp")
	consumed = {r.item_code: r for r in frappe.db.sql("""
		SELECT bm.item_code, bm.material_type, bm.uom,
		       SUM(bm.actual_qty) actual, SUM(bm.target_qty) target, SUM(bm.amount) cost
		FROM `tabBatch Material` bm
		JOIN `tabBatch Production` bp ON bp.name = bm.parent
		WHERE bp.docstatus = 1 AND {where}
		GROUP BY bm.item_code, bm.material_type, bm.uom
	""".format(where=cwhere), cparams, as_dict=True)}

	pwhere, pparams = build_conditions(
		filters, {"material_type": "mi.material_type", "plant": "mi.plant"},
		date_field="inward_date", alias="mi")
	bought = {r.item_code: r for r in frappe.db.sql("""
		SELECT mi.item_code, SUM(mi.net_weight) * 1000 qty, SUM(mi.amount) value,
		       COUNT(mi.name) trucks
		FROM `tabMaterial Inward` mi
		WHERE mi.docstatus = 1 AND {where}
		GROUP BY mi.item_code
	""".format(where=pwhere), pparams, as_dict=True)}

	produced = flt(frappe.db.sql("""
		SELECT SUM(qty_m3) FROM `tabBatch Production`
		WHERE docstatus = 1 AND production_date BETWEEN %(from_date)s AND %(to_date)s""",
		{"from_date": filters.get("from_date"), "to_date": filters.get("to_date")})[0][0])

	data = []
	for item in sorted(set(list(consumed) + list(bought))):
		c = consumed.get(item)
		b = bought.get(item)
		silo = frappe.db.get_value("Silo", {"item_code": item},
		                           ["name", "warehouse", "min_level_mt"], as_dict=True)
		on_hand = flt(frappe.db.get_value(
			"Bin", {"item_code": item, "warehouse": silo.warehouse}, "actual_qty")) if silo else 0
		used = flt(c.actual) if c else 0
		data.append([
			item, (c.material_type if c else None) or frappe.db.get_value(
				"Silo", {"item_code": item}, "material_type"),
			(c.uom if c else frappe.db.get_value("Item", item, "stock_uom")),
			flt(c.target) if c else 0, used,
			(100.0 * (used - flt(c.target)) / flt(c.target)) if c and flt(c.target) else 0,
			flt(c.cost) if c else 0,
			(used / produced) if produced else 0,
			(b.trucks if b else 0), flt(b.qty) if b else 0, flt(b.value) if b else 0,
			on_hand,
			(on_hand / (used / 30.0)) if used else None,
		])

	columns = [
		col("Item", "Link", 175, options="Item"), col("Type", "Data", 100),
		col("UOM", "Data", 70),
		col("Recipe Qty", "Float", 115, precision=1),
		col("Consumed", "Float", 115, precision=1),
		col("Variance Pct", "Percent", 110),
		col("Consumption Cost", "Currency", 140),
		col("Per m3 of Concrete", "Float", 140, precision=2),
		col("Trucks In", "Int", 90), col("Bought Qty", "Float", 115, precision=1),
		col("Purchase Value", "Currency", 135),
		col("On Hand", "Float", 105, precision=1),
		col("Days Cover", "Float", 105, precision=1),
	]

	chart = {"data": {"labels": [d[0] for d in data],
	                  "datasets": [{"name": "Consumed", "values": [round(d[4], 0) for d in data]},
	                               {"name": "Bought", "values": [round(d[9], 0) for d in data]}]},
	         "type": "bar", "colors": ["#B45309", "#0D9488"]}

	summary = [
		{"label": "Consumption cost", "value": round(sum(d[6] for d in data), 2),
		 "datatype": "Currency", "indicator": "Orange"},
		{"label": "Purchase value", "value": round(sum(d[10] for d in data), 2),
		 "datatype": "Currency", "indicator": "Blue"},
		{"label": "Concrete produced m3", "value": round(produced, 2),
		 "indicator": "Green"},
	]
	return columns, data, None, chart, summary

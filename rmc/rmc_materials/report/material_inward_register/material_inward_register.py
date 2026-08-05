# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Every weighbridge ticket, with the purchase receipt it posted."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	where, params = build_conditions(
		filters, {"plant": "mi.plant", "vehicle_no": "mi.vehicle_no", "supplier": "mi.supplier", "item_code": "mi.item_code",
		          "silo": "mi.silo", "material_type": "mi.material_type"},
		date_field="inward_date", alias="mi")

	rows = frappe.db.sql("""
		SELECT mi.name, mi.inward_date, mi.supplier, mi.item_code, mi.material_type,
		       mi.vehicle_no, mi.gross_weight, mi.tare_weight, mi.net_weight,
		       mi.rate, mi.amount, mi.silo, mi.purchase_receipt
		FROM `tabMaterial Inward` mi
		WHERE mi.docstatus = 1 AND {where}
		ORDER BY mi.inward_date DESC, mi.name DESC
	""".format(where=where), params, as_dict=True)

	data = [[r.name, r.inward_date, r.supplier, r.item_code, r.material_type,
	         r.vehicle_no, flt(r.gross_weight), flt(r.tare_weight), flt(r.net_weight),
	         flt(r.rate), flt(r.amount), r.silo, r.purchase_receipt] for r in rows]

	columns = [
		col("Inward", "Link", 130, options="Material Inward"),
		col("Date", "Date", 95), col("Supplier", "Link", 170, options="Supplier"),
		col("Item", "Link", 175, options="Item"), col("Type", "Data", 95),
		col("Vehicle", "Data", 110),
		col("Gross MT", "Float", 95, precision=3),
		col("Tare MT", "Float", 95, precision=3),
		col("Net MT", "Float", 95, precision=3),
		col("Rate", "Currency", 95), col("Amount", "Currency", 120),
		col("Silo", "Link", 140, options="Silo"),
		col("Purchase Receipt", "Link", 150, options="Purchase Receipt"),
	]

	by_type = {}
	for d in data:
		by_type[d[4] or "Other"] = by_type.get(d[4] or "Other", 0) + d[8]
	chart = {"data": {"labels": list(by_type),
	                  "datasets": [{"name": "Net MT", "values":
	                                [round(v, 2) for v in by_type.values()]}]},
	         "type": "bar", "colors": ["#EA580C"]}

	summary = [
		{"label": "Trucks", "value": len(data), "indicator": "Blue"},
		{"label": "Net MT received", "value": round(sum(d[8] for d in data), 2),
		 "indicator": "Green"},
		{"label": "Purchase value", "value": round(sum(d[10] for d in data), 2),
		 "datatype": "Currency", "indicator": "Orange"},
	]
	return columns, data, None, chart, summary

# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""What each supplier delivered, at what rate, and what it cost."""

import frappe
from frappe.utils import flt

from rmc.report_utils import build_conditions, col


def execute(filters=None):
	filters = frappe._dict(filters or {})
	where, params = build_conditions(
		filters, {"supplier": "mi.supplier", "material_type": "mi.material_type"},
		date_field="inward_date", alias="mi")

	rows = frappe.db.sql("""
		SELECT mi.supplier, mi.item_code, mi.material_type, COUNT(mi.name) trucks,
		       SUM(mi.net_weight) mt, AVG(mi.rate) rate, SUM(mi.amount) value,
		       MIN(mi.inward_date) first_in, MAX(mi.inward_date) last_in
		FROM `tabMaterial Inward` mi
		WHERE mi.docstatus = 1 AND {where}
		GROUP BY mi.supplier, mi.item_code, mi.material_type
		ORDER BY SUM(mi.amount) DESC
	""".format(where=where), params, as_dict=True)

	data = [[r.supplier, r.item_code, r.material_type, r.trucks, flt(r.mt),
	         flt(r.mt) / r.trucks if r.trucks else 0, flt(r.rate), flt(r.value),
	         r.first_in, r.last_in] for r in rows]

	columns = [
		col("Supplier", "Link", 190, options="Supplier"),
		col("Item", "Link", 175, options="Item"), col("Type", "Data", 100),
		col("Trucks", "Int", 80), col("Net MT", "Float", 105, precision=2),
		col("Avg Load MT", "Float", 115, precision=2),
		col("Avg Rate", "Currency", 110), col("Value", "Currency", 130),
		col("First Inward", "Date", 110), col("Last Inward", "Date", 110),
	]

	by_sup = {}
	for d in data:
		by_sup[d[0]] = by_sup.get(d[0], 0) + d[7]
	top = sorted(by_sup.items(), key=lambda kv: -kv[1])[:10]
	chart = {"data": {"labels": [k[:22] for k, _v in top],
	                  "datasets": [{"name": "Purchase value",
	                                "values": [round(v, 0) for _k, v in top]}]},
	         "type": "bar", "colors": ["#B91C1C"]}

	summary = [
		{"label": "Suppliers", "value": len(by_sup), "indicator": "Blue"},
		{"label": "Net MT", "value": round(sum(d[4] for d in data), 2), "indicator": "Green"},
		{"label": "Purchase value", "value": round(sum(d[7] for d in data), 2),
		 "datatype": "Currency", "indicator": "Orange"},
	]
	return columns, data, None, chart, summary

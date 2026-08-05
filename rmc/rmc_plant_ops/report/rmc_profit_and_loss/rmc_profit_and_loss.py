# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""RMC Profit and Loss — the plant's operating result, straight off the GL.

Not a parallel calculation: every figure is read from GL Entry, so it ties to
ERPNext's own Profit and Loss statement to the paisa. The operating lines
underneath (m³ sold, realisation, cost per m³) come from the RMC documents that
raised those entries, which is what makes it readable to a plant manager rather
than to an accountant.
"""

import frappe
from frappe.utils import flt

from rmc.report_utils import col


def _gl(from_date, to_date, root_type, cost_center=None):
	cond = ""
	params = {"from_date": from_date, "to_date": to_date, "root_type": root_type}
	if cost_center:
		cond = " AND gle.cost_center = %(cost_center)s"
		params["cost_center"] = cost_center
	return frappe.db.sql("""
		SELECT gle.account, a.account_name,
		       ROUND(SUM(gle.credit) - SUM(gle.debit), 2) credit_net,
		       ROUND(SUM(gle.debit) - SUM(gle.credit), 2) debit_net
		FROM `tabGL Entry` gle
		JOIN `tabAccount` a ON a.name = gle.account
		WHERE gle.is_cancelled = 0 AND a.root_type = %(root_type)s
		  AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
		""" + cond + """
		GROUP BY gle.account, a.account_name
		HAVING ABS(SUM(gle.debit) - SUM(gle.credit)) > 0.005
		ORDER BY ABS(SUM(gle.debit) - SUM(gle.credit)) DESC
	""", params, as_dict=True)


def execute(filters=None):
	filters = frappe._dict(filters or {})
	frm, to = filters.get("from_date"), filters.get("to_date")
	cc = filters.get("cost_center")

	income = _gl(frm, to, "Income", cc)
	expense = _gl(frm, to, "Expense", cc)
	revenue = sum(flt(r.credit_net) for r in income)
	cost = sum(flt(r.debit_net) for r in expense)

	# the operating side, from the documents that created those entries
	ops = frappe.db.sql("""
		SELECT COUNT(*) loads, SUM(qty_m3) qty, SUM(amount) value
		FROM `tabDelivery Challan`
		WHERE docstatus = 1 AND challan_date BETWEEN %(f)s AND %(t)s""",
		{"f": frm, "t": to}, as_dict=True)[0]
	made = frappe.db.sql("""
		SELECT SUM(qty_m3) qty, SUM(total_material_cost) cost
		FROM `tabBatch Production`
		WHERE docstatus = 1 AND production_date BETWEEN %(f)s AND %(t)s""",
		{"f": frm, "t": to}, as_dict=True)[0]

	data = []

	def line(label, value, indent=0, bold=0, kind=""):
		data.append({"particulars": ("&nbsp;" * 4 * indent) + label, "amount": value,
		             "bold": bold, "kind": kind})

	line("<b>INCOME</b>", None, bold=1)
	for r in income:
		line(r.account_name or r.account, flt(r.credit_net), indent=1)
	line("<b>Total Income</b>", revenue, bold=1)

	line("", None)
	line("<b>EXPENSES</b>", None, bold=1)
	for r in expense:
		line(r.account_name or r.account, flt(r.debit_net), indent=1)
	line("<b>Total Expenses</b>", cost, bold=1)

	line("", None)
	line("<b>PROFIT / (LOSS)</b>", revenue - cost, bold=1)

	line("", None)
	line("<b>OPERATING NUMBERS</b>", None, bold=1)
	qty = flt(ops.qty)
	line("Concrete sold (m³)", qty, indent=1)
	line("Loads dispatched", flt(ops.loads), indent=1)
	line("Realisation per m³", (revenue / qty) if qty else 0, indent=1)
	line("Cost per m³ (all expenses)", (cost / qty) if qty else 0, indent=1)
	line("Margin per m³", ((revenue - cost) / qty) if qty else 0, indent=1)
	line("Concrete produced (m³)", flt(made.qty), indent=1)
	line("Material cost booked on batches", flt(made.cost), indent=1)

	columns = [
		col("Particulars", "Data", 340),
		col("Amount", "Currency", 180),
	]

	chart = {"data": {"labels": ["Income", "Expenses", "Profit"],
	                  "datasets": [{"name": "₹",
	                                "values": [round(revenue, 2), round(cost, 2),
	                                           round(revenue - cost, 2)]}]},
	         "type": "bar", "colors": ["#0F766E"]}

	summary = [
		{"label": "Income", "value": round(revenue, 2), "datatype": "Currency",
		 "indicator": "Green"},
		{"label": "Expenses", "value": round(cost, 2), "datatype": "Currency",
		 "indicator": "Red"},
		{"label": "Profit", "value": round(revenue - cost, 2), "datatype": "Currency",
		 "indicator": "Blue" if revenue >= cost else "Red"},
		{"label": "Margin",
		 "value": round(100.0 * (revenue - cost) / revenue, 1) if revenue else 0,
		 "datatype": "Percent", "indicator": "Orange"},
	]
	return columns, data, None, chart, summary

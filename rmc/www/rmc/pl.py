"""Public P&L page — the plant's result, read straight off the general ledger."""

import frappe
from frappe.utils import flt

from rmc.www.rmc.index import common, money

no_cache = 1


def _accounts(frm, to, root_type):
	return frappe.db.sql("""
		SELECT a.account_name, gle.account,
		       ROUND(SUM(gle.credit) - SUM(gle.debit), 2) cr,
		       ROUND(SUM(gle.debit) - SUM(gle.credit), 2) dr
		FROM `tabGL Entry` gle JOIN `tabAccount` a ON a.name = gle.account
		WHERE gle.is_cancelled = 0 AND a.root_type = %(rt)s
		  AND gle.posting_date BETWEEN %(f)s AND %(t)s
		GROUP BY gle.account, a.account_name
		HAVING ABS(SUM(gle.debit) - SUM(gle.credit)) > 0.005
		ORDER BY ABS(SUM(gle.debit) - SUM(gle.credit)) DESC""",
		{"rt": root_type, "f": frm, "t": to}, as_dict=True)


def get_context(context):
	frm, to = common(context)
	context.title = "Profit & Loss"

	income = _accounts(frm, to, "Income")
	expense = _accounts(frm, to, "Expense")
	revenue = sum(flt(r.cr) for r in income)
	cost = sum(flt(r.dr) for r in expense)
	profit = revenue - cost

	for r in income:
		r.amount_h = money(r.cr)
		r.pct = round(100.0 * flt(r.cr) / revenue, 1) if revenue else 0
	for r in expense:
		r.amount_h = money(r.dr)
		r.pct = round(100.0 * flt(r.dr) / cost, 1) if cost else 0

	context.income = income
	context.expense = expense
	context.revenue_h = money(revenue)
	context.cost_h = money(cost)
	context.profit_h = money(profit)
	context.profit_positive = profit >= 0
	context.margin = round(100.0 * profit / revenue, 1) if revenue else 0

	ops = frappe.db.sql("""
		SELECT COUNT(*) loads, SUM(qty_m3) qty FROM `tabDelivery Challan`
		WHERE docstatus = 1 AND challan_date BETWEEN %(f)s AND %(t)s""",
		{"f": frm, "t": to}, as_dict=True)[0]
	qty = flt(ops.qty)
	context.ops = [
		("Concrete sold", "%s m³" % qty),
		("Loads dispatched", ops.loads or 0),
		("Realisation per m³", "₹ %s" % money(revenue / qty if qty else 0)),
		("Cost per m³", "₹ %s" % money(cost / qty if qty else 0)),
		("Margin per m³", "₹ %s" % money(profit / qty if qty else 0)),
	]

	# receivables sit on the balance sheet, but it is the first thing an owner asks
	context.outstanding_h = money(flt(frappe.db.sql("""
		SELECT SUM(outstanding_amount) FROM `tabSales Invoice` WHERE docstatus = 1""")[0][0]))

"""Context for the public RMC pages.

These are website pages, not desk pages: a customer, an owner on a phone or a
projector in the plant office can open them without an ERPNext login. They read
the same documents and the same GL the desk does, so the numbers can never
disagree — there is no second copy of anything here.
"""

import frappe
from frappe.utils import add_days, flt, get_first_day, getdate, nowdate

no_cache = 1


def _range(period):
	today = getdate(nowdate())
	if period == "today":
		return today, today, "Today"
	if period == "yesterday":
		y = add_days(today, -1)
		return y, y, "Yesterday"
	if period == "last_month":
		start = get_first_day(add_days(get_first_day(today), -1))
		return start, add_days(get_first_day(today), -1), "Last Month"
	if period == "last_90":
		return add_days(today, -89), today, "Last 90 Days"
	if period == "this_month":
		return get_first_day(today), today, "This Month"
	return add_days(today, -29), today, "Last 30 Days"


def common(context, period=None):
	period = period or frappe.form_dict.get("period") or "last_30"
	frm, to, label = _range(period)
	context.period = period
	context.period_label = label
	context.from_date = frm
	context.to_date = to
	context.periods = [
		("today", "Today"), ("yesterday", "Yesterday"), ("this_month", "This Month"),
		("last_month", "Last Month"), ("last_30", "Last 30 Days"), ("last_90", "Last 90 Days"),
	]
	context.company = frappe.db.get_single_value("RMC Settings", "company") or "Midhuna RMC"
	context.plant = frappe.db.get_single_value("RMC Settings", "default_plant") or ""
	context.now = frappe.utils.now_datetime().strftime("%d %b %Y, %H:%M")
	return frm, to


def money(v):
	"""Indian short form — a plant owner reads 1.06 Cr, not 10603402.75."""
	v = flt(v)
	if abs(v) >= 1e7:
		return "%.2f Cr" % (v / 1e7)
	if abs(v) >= 1e5:
		return "%.2f L" % (v / 1e5)
	return "{:,.0f}".format(v)


def get_context(context):
	frm, to = common(context)

	sales = frappe.db.sql("""
		SELECT COUNT(*) loads, SUM(qty_m3) qty, SUM(amount) value,
		       COUNT(DISTINCT customer) customers
		FROM `tabDelivery Challan`
		WHERE docstatus = 1 AND challan_date BETWEEN %(f)s AND %(t)s""",
		{"f": frm, "t": to}, as_dict=True)[0]
	prod = frappe.db.sql("""
		SELECT COUNT(*) batches, SUM(qty_m3) qty, SUM(total_material_cost) cost
		FROM `tabBatch Production`
		WHERE docstatus = 1 AND production_date BETWEEN %(f)s AND %(t)s""",
		{"f": frm, "t": to}, as_dict=True)[0]
	buy = frappe.db.sql("""
		SELECT COUNT(*) trucks, SUM(net_weight) mt, SUM(amount) value
		FROM `tabMaterial Inward`
		WHERE docstatus = 1 AND inward_date BETWEEN %(f)s AND %(t)s""",
		{"f": frm, "t": to}, as_dict=True)[0]

	revenue = flt(frappe.db.sql("""
		SELECT SUM(gle.credit) - SUM(gle.debit) FROM `tabGL Entry` gle
		JOIN `tabAccount` a ON a.name = gle.account
		WHERE gle.is_cancelled = 0 AND a.root_type = 'Income'
		  AND gle.posting_date BETWEEN %(f)s AND %(t)s""",
		{"f": frm, "t": to})[0][0])
	expense = flt(frappe.db.sql("""
		SELECT SUM(gle.debit) - SUM(gle.credit) FROM `tabGL Entry` gle
		JOIN `tabAccount` a ON a.name = gle.account
		WHERE gle.is_cancelled = 0 AND a.root_type = 'Expense'
		  AND gle.posting_date BETWEEN %(f)s AND %(t)s""",
		{"f": frm, "t": to})[0][0])

	context.kpis = [
		("Concrete sold", "%s m³" % flt(sales.qty), "%d loads · %d customers"
		 % (sales.loads or 0, sales.customers or 0), "sale"),
		("Sales value", "₹ " + money(sales.value), "avg ₹ %s / m³"
		 % money(flt(sales.value) / flt(sales.qty) if flt(sales.qty) else 0), "sale"),
		("Produced", "%s m³" % flt(prod.qty), "%d batches" % (prod.batches or 0), "prod"),
		("Material bought", "₹ " + money(buy.value), "%d trucks · %s MT"
		 % (buy.trucks or 0, round(flt(buy.mt), 1)), "buy"),
		("Book income", "₹ " + money(revenue), "from the general ledger", "pl"),
		("Book profit", "₹ " + money(revenue - expense),
		 "%.1f%% of income" % (100.0 * (revenue - expense) / revenue if revenue else 0), "pl"),
	]

	context.by_grade = frappe.db.sql("""
		SELECT grade, SUM(qty_m3) qty, SUM(amount) value
		FROM `tabDelivery Challan`
		WHERE docstatus = 1 AND challan_date BETWEEN %(f)s AND %(t)s
		GROUP BY grade ORDER BY SUM(qty_m3) DESC""", {"f": frm, "t": to}, as_dict=True)
	top = flt(max([g.qty for g in context.by_grade], default=1))
	for g in context.by_grade:
		g.pct = round(100.0 * flt(g.qty) / top, 1)
		g.value_h = money(g.value)

	context.daily = frappe.db.sql("""
		SELECT challan_date d, SUM(qty_m3) qty, SUM(amount) value
		FROM `tabDelivery Challan`
		WHERE docstatus = 1 AND challan_date BETWEEN %(f)s AND %(t)s
		GROUP BY challan_date ORDER BY challan_date""", {"f": frm, "t": to}, as_dict=True)
	peak = flt(max([d.qty for d in context.daily], default=1))
	for d in context.daily:
		d.pct = round(100.0 * flt(d.qty) / peak, 1)

	context.customers = frappe.db.sql("""
		SELECT customer, SUM(qty_m3) qty, SUM(amount) value, COUNT(*) loads
		FROM `tabDelivery Challan`
		WHERE docstatus = 1 AND challan_date BETWEEN %(f)s AND %(t)s
		GROUP BY customer ORDER BY SUM(amount) DESC LIMIT 8""",
		{"f": frm, "t": to}, as_dict=True)
	for c in context.customers:
		c.value_h = money(c.value)

	context.money = money

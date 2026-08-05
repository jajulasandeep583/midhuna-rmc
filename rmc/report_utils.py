"""Shared pieces for the RMC script reports.

Every report offers the same shape of filter (a date range plus whatever
dimension it is about), so the SQL-building is done once here.
"""

import frappe
from frappe.utils import add_days, getdate, nowdate


def default_range(days=30):
	"""From/to defaults: the last month, ending today."""
	to_date = getdate(nowdate())
	return add_days(to_date, -(days - 1)), to_date


def date_filters(fieldname="posting_date", label="Date"):
	frm, to = default_range()
	return [
		{"fieldname": "from_date", "label": "From Date", "fieldtype": "Date",
		 "default": frm, "reqd": 1},
		{"fieldname": "to_date", "label": "To Date", "fieldtype": "Date",
		 "default": to, "reqd": 1},
	]


def link_filter(fieldname, label, options, reqd=0):
	return {"fieldname": fieldname, "label": label, "fieldtype": "Link",
	        "options": options, "reqd": reqd}


def select_filter(fieldname, label, options, default=None):
	f = {"fieldname": fieldname, "label": label, "fieldtype": "Select",
	     "options": options}
	if default:
		f["default"] = default
	return f


def build_conditions(filters, mapping, date_field=None, alias=""):
	"""Turn the filter dict into a WHERE fragment plus its parameters.

	mapping: {filter fieldname: sql column}. Empty filters are skipped, so a
	report with nothing selected still returns the whole range.
	"""
	conds, params = [], {}
	prefix = ("%s." % alias) if alias else ""

	if date_field and filters.get("from_date"):
		conds.append("%s%s >= %%(from_date)s" % (prefix, date_field))
		params["from_date"] = filters["from_date"]
	if date_field and filters.get("to_date"):
		conds.append("%s%s <= %%(to_date)s" % (prefix, date_field))
		params["to_date"] = filters["to_date"]

	for key, column in mapping.items():
		value = filters.get(key)
		if value in (None, "", []):
			continue
		conds.append("%s = %%(%s)s" % (column, key))
		params[key] = value

	return (" AND ".join(conds) or "1=1"), params


def col(label, fieldtype="Data", width=120, options=None, precision=None):
	c = {"label": label, "fieldname": frappe.scrub(label), "fieldtype": fieldtype,
	     "width": width}
	if options:
		c["options"] = options
	if precision:
		c["precision"] = precision
	return c

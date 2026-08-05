// Copyright (c) 2026, Midhuna Tech and contributors
// For license information, please see license.txt

frappe.query_reports["Slump Compliance"] = {
	filters: [
		rmc.period_filter("Last 90 Days"),
		{
			fieldname: "from_date", label: __("From Date"), fieldtype: "Date",
			default: frappe.datetime.add_days(frappe.datetime.get_today(), -30), reqd: 1,
		},
		{
			fieldname: "to_date", label: __("To Date"), fieldtype: "Date",
			default: frappe.datetime.get_today(), reqd: 1,
		},
		{ fieldname: "grade", label: __("Grade"), fieldtype: "Link", options: "Concrete Grade" },
		{ fieldname: "customer", label: __("Customer"), fieldtype: "Link", options: "Customer" },
		{ fieldname: "only_out", label: __("Only loads outside tolerance"), fieldtype: "Check" },
	],
};

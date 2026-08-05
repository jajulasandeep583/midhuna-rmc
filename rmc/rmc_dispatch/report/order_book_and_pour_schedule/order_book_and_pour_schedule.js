// Copyright (c) 2026, Midhuna Tech and contributors
// For license information, please see license.txt

frappe.query_reports["Order Book and Pour Schedule"] = {
	filters: [
		rmc.period_filter("Last 30 Days"),
		{
			fieldname: "from_date", label: __("From Date"), fieldtype: "Date",
			default: frappe.datetime.add_days(frappe.datetime.get_today(), -30), reqd: 1,
		},
		{
			fieldname: "to_date", label: __("To Date"), fieldtype: "Date",
			default: frappe.datetime.get_today(), reqd: 1,
		},
		{ fieldname: "customer", label: __("Customer"), fieldtype: "Link", options: "Customer" },
		{ fieldname: "grade", label: __("Grade"), fieldtype: "Link", options: "Concrete Grade" },
		{ fieldname: "only_pending", label: __("Only pours not yet fully delivered"), fieldtype: "Check" },
	],
};

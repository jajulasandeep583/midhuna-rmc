// Copyright (c) 2026, Midhuna Tech and contributors
// For license information, please see license.txt

frappe.query_reports["Power and Diesel Consumption"] = {
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
		{ fieldname: "plant", label: __("Plant"), fieldtype: "Link", options: "RMC Plant" },
	],
};

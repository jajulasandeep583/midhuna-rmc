// Copyright (c) 2026, Midhuna Tech and contributors
// For license information, please see license.txt

frappe.query_reports["RMC Profit and Loss"] = {
	filters: [
		rmc.period_filter("This Month"),
		{
			fieldname: "from_date", label: __("From Date"), fieldtype: "Date",
			default: frappe.datetime.month_start(), reqd: 1,
		},
		{
			fieldname: "to_date", label: __("To Date"), fieldtype: "Date",
			default: frappe.datetime.get_today(), reqd: 1,
		},
		{
			fieldname: "cost_center", label: __("Cost Center"), fieldtype: "Link",
			options: "Cost Center",
		},
	],

	// the section headings and totals carry a bold flag from the server
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.bold) {
			value = "<b>" + value + "</b>";
		}
		return value;
	},
};

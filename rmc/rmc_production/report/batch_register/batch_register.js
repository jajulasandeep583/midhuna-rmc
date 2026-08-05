// Copyright (c) 2026, Midhuna Tech and contributors
// For license information, please see license.txt

frappe.query_reports["Batch Register"] = {
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
		{ fieldname: "grade", label: __("Grade"), fieldtype: "Link", options: "Concrete Grade" },
		{ fieldname: "concrete_order", label: __("Concrete Order"), fieldtype: "Link", options: "Concrete Order" },
		{ fieldname: "shift", label: __("Shift"), fieldtype: "Select", options: "\nShift A\nShift B\nShift C" },
		{ fieldname: "operator", label: __("Operator"), fieldtype: "Data" },
		{ fieldname: "status", label: __("Status"), fieldtype: "Select", options: "\nDraft\nProduced\nDispatched\nCancelled" },
	],
};

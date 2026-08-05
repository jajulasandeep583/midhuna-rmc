// Copyright (c) 2026, Midhuna Tech and contributors
// For license information, please see license.txt

frappe.query_reports["Breakdown and Maintenance Log"] = {
	filters: [
		{
			fieldname: "from_date", label: __("From Date"), fieldtype: "Date",
			default: frappe.datetime.add_days(frappe.datetime.get_today(), -30), reqd: 1,
		},
		{
			fieldname: "to_date", label: __("To Date"), fieldtype: "Date",
			default: frappe.datetime.get_today(), reqd: 1,
		},
		{ fieldname: "plant", label: __("Plant"), fieldtype: "Link", options: "RMC Plant" },
		{ fieldname: "equipment", label: __("Equipment"), fieldtype: "Select", options: "\nBatching Plant\nMixer\nConveyor\nCement Silo\nWeighing System\nWater System\nAir Compressor\nDG Set\nTransit Mixer\nConcrete Pump\nOther" },
		{ fieldname: "status", label: __("Status"), fieldtype: "Select", options: "\nOpen\nIn Progress\nClosed" },
		{ fieldname: "severity", label: __("Severity"), fieldtype: "Select", options: "\nLow\nMedium\nHigh" },
	],
};

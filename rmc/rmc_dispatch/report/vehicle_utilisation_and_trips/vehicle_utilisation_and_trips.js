// Copyright (c) 2026, Midhuna Tech and contributors
// For license information, please see license.txt

frappe.query_reports["Vehicle Utilisation and Trips"] = {
	filters: [
		{
			fieldname: "from_date", label: __("From Date"), fieldtype: "Date",
			default: frappe.datetime.add_days(frappe.datetime.get_today(), -30), reqd: 1,
		},
		{
			fieldname: "to_date", label: __("To Date"), fieldtype: "Date",
			default: frappe.datetime.get_today(), reqd: 1,
		},
		{ fieldname: "transit_mixer", label: __("Transit Mixer"), fieldtype: "Link", options: "Transit Mixer" },
		{ fieldname: "vehicle_type", label: __("Vehicle Type"), fieldtype: "Select", options: "\nTransit Mixer\nConcrete Pump\nLoader\nTipper" },
		{ fieldname: "customer", label: __("Customer"), fieldtype: "Link", options: "Customer" },
	],
};

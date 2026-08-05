// Copyright (c) 2026, Midhuna Tech and contributors
// For license information, please see license.txt

frappe.query_reports["Silo and Stock Status"] = {
	filters: [
		{ fieldname: "material_type", label: __("Material Type"), fieldtype: "Select", options: "\nCement\nSand\nAggregate\nFly Ash\nGGBS\nAdmixture\nWater" },
		{ fieldname: "only_low", label: __("Only silos at or below the alert level"), fieldtype: "Check" },
	],
};

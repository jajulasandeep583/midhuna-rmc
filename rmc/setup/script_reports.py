"""Turn the RMC reports into Script Reports with real filters.

Query Reports cannot take filters, so every one of them dumped the whole month
and left the user to scroll. These are proper Script Reports: a date range,
plant, grade, customer or vehicle filter, sensible column types, and a chart
where one helps.

The Python lives in <module>/report/<name>/<name>.py inside the app; this
module only creates/repoints the Report records.

    bench --site rmc.local execute rmc.setup.script_reports.install
"""

import frappe

# (report name, module, ref doctype)
REPORTS = [
	("Daily Production Summary", "RMC Production", "Batch Production"),
	("Batch Register", "RMC Production", "Batch Production"),
	("Material Consumption vs Recipe", "RMC Production", "Batch Production"),
	("Production Target vs Actual", "RMC Production", "Concrete Order"),
	("Cube Test Register", "RMC Production", "Cube Test"),
	("Material Inward Register", "RMC Materials", "Material Inward"),
	("Silo and Stock Status", "RMC Materials", "Silo"),
	("Dispatch Register", "RMC Dispatch", "Delivery Challan"),
	("Customer Order Status", "RMC Dispatch", "Concrete Order"),
	("Vehicle Utilisation and Trips", "RMC Dispatch", "Delivery Challan"),
	("Customer Wise Sales", "RMC Dispatch", "Delivery Challan"),
	("Plant Availability and Downtime", "RMC Plant Ops", "Plant Status Log"),
	("Power and Diesel Consumption", "RMC Plant Ops", "Power Log"),
	("Breakdown and Maintenance Log", "RMC Plant Ops", "Breakdown Log"),
	# second wave
	("Order Book and Pour Schedule", "RMC Dispatch", "Concrete Order"),
	("Supplier Purchase Summary", "RMC Materials", "Material Inward"),
	("Driver Performance", "RMC Dispatch", "Delivery Challan"),
	("Slump Compliance", "RMC Production", "Delivery Challan"),
	("Grade Profitability", "RMC Production", "Delivery Challan"),
	("Monthly Plant Summary", "RMC Plant Ops", "Batch Production"),
	# third wave — productivity, the sales register and the purchase manager's page
	("Plant Productivity", "RMC Plant Ops", "Batch Production"),
	("Concrete Sales Register", "RMC Dispatch", "Sales Invoice"),
	("Raw Material Consumption Summary", "RMC Materials", "Batch Production"),
	# reads the GL directly, so it ties to ERPNext own P&L to the paisa
	("RMC Profit and Loss", "RMC Plant Ops", "GL Entry"),
]

ROLES = ("System Manager", "RMC Manager", "Plant Operator",
         "Dispatch Incharge", "Quality Engineer", "RMC Accounts")


def install():
	made, changed = [], []
	for name, module, ref in REPORTS:
		if not frappe.db.exists("DocType", ref):
			continue
		if frappe.db.exists("Report", name):
			doc = frappe.get_doc("Report", name)
			if doc.report_type != "Script Report":
				doc.report_type = "Script Report"
				doc.query = ""
				changed.append(name)
			doc.module = module
			doc.ref_doctype = ref
			doc.is_standard = "Yes"
			doc.disabled = 0
			doc.flags.ignore_permissions = True
			doc.save()
			continue
		frappe.get_doc({
			"doctype": "Report", "report_name": name, "ref_doctype": ref,
			"module": module, "report_type": "Script Report", "is_standard": "Yes",
			"disabled": 0,
			"roles": [{"role": r} for r in ROLES if frappe.db.exists("Role", r)],
		}).insert(ignore_permissions=True)
		made.append(name)

	frappe.db.commit()
	frappe.clear_cache()
	print("  + script reports created: %d, converted from query: %d"
	      % (len(made), len(changed)))
	return {"created": made, "converted": changed}

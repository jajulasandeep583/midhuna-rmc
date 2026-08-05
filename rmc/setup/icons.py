"""Give every RMC doctype, workspace, shortcut and sidebar link its own icon.

The glyphs live in public/icons/rmc-icons.svg and are loaded through the
app_include_icons hook, so they colour themselves like any other desk icon and
follow the light/dark theme.
"""

import frappe

DOCTYPE_ICONS = {
	# setup
	"RMC Plant": "rmc-plant",
	"Concrete Grade": "rmc-grade",
	"Mix Design": "rmc-mix",
	"Transit Mixer": "rmc-mixer",
	"Construction Site": "rmc-site",
	"Silo": "rmc-silo",
	"RMC Settings": "rmc-settings",
	# materials
	"Material Inward": "rmc-inward",
	# production
	"Batch Production": "rmc-batch",
	"Cube Test": "rmc-cube-test",
	# dispatch
	"Concrete Order": "rmc-order",
	"Delivery Challan": "rmc-challan",
	# plant ops
	"Plant Status Log": "rmc-status",
	"Breakdown Log": "rmc-breakdown",
	"RMC Maintenance Task": "rmc-maintenance",
	"Power Log": "rmc-power",
}

WORKSPACE_ICONS = {
	"RMC Dashboard": "rmc-dashboard",
	"RMC Production": "rmc-batch",
	"RMC Materials": "rmc-silo",
	"RMC Dispatch": "rmc-dispatch",
	"RMC Quality": "rmc-quality",
	"RMC Setup": "rmc-settings",
}

# Anything else that appears as a link, shortcut or page label.
EXTRA_ICONS = {
	# standard doctypes we link to
	"Customer": "rmc-customer",
	"Supplier": "rmc-supplier",
	"Driver": "rmc-driver",
	"Item": "rmc-cement",
	"Stock Entry": "rmc-stock",
	"Purchase Receipt": "rmc-inward",
	"Sales Invoice": "rmc-invoice",
	"Stock Reconciliation": "rmc-stock",
	# desk pages
	"Live Plant Dashboard": "rmc-dashboard",
	"RMC Control Tower": "rmc-dashboard",
	"Batching Board": "rmc-batch",
	"Dispatch Board": "rmc-dispatch",
	"Order 360": "rmc-order",
	"Silo & Stock Board": "rmc-silo",
	"Quality Board": "rmc-quality",
	"How to Use RMC": "rmc-guide",
	# reports, by name
	"Daily Production Summary": "rmc-report",
	"Batch Register": "rmc-batch",
	"Material Consumption vs Recipe": "rmc-mix",
	"Production Target vs Actual": "rmc-report",
	"Material Inward Register": "rmc-inward",
	"Silo and Stock Status": "rmc-silo",
	"Dispatch Register": "rmc-challan",
	"Customer Order Status": "rmc-order",
	"Vehicle Utilisation and Trips": "rmc-cycle",
	"Customer Wise Sales": "rmc-invoice",
	"Cube Test Register": "rmc-cube-test",
	"Plant Availability and Downtime": "rmc-status",
	"Power and Diesel Consumption": "rmc-power",
	"Breakdown and Maintenance Log": "rmc-breakdown",
	# link-group headings
	"Daily Operations": "rmc-batch",
	"MIS Reports": "rmc-report",
	"Setup": "rmc-settings",
	"Production": "rmc-batch",
	"Recipes": "rmc-mix",
	"Reports": "rmc-report",
	"Inward & Stock": "rmc-inward",
	"Dispatch": "rmc-dispatch",
	"Customers": "rmc-customer",
	"Quality": "rmc-quality",
	"Plant Operations": "rmc-status",
	"Plant Masters": "rmc-plant",
	"Product Masters": "rmc-grade",
	"Fleet & Customers": "rmc-mixer",
}


def icon_for(label):
	return (DOCTYPE_ICONS.get(label) or EXTRA_ICONS.get(label)
	        or WORKSPACE_ICONS.get(label))


def install():
	n_dt = 0
	for dt, icon in DOCTYPE_ICONS.items():
		if frappe.db.exists("DocType", dt):
			frappe.db.set_value("DocType", dt, "icon", icon, update_modified=False)
			n_dt += 1

	n_ws = 0
	for ws, icon in WORKSPACE_ICONS.items():
		if not frappe.db.exists("Workspace", ws):
			continue
		doc = frappe.get_doc("Workspace", ws)
		doc.icon = icon
		for row in doc.links:
			ic = icon_for(row.label) or icon_for(row.link_to)
			if ic:
				row.icon = ic
		for row in doc.shortcuts:
			ic = icon_for(row.label) or icon_for(row.link_to)
			if ic:
				row.icon = ic
		doc.flags.ignore_permissions = True
		doc.save()
		n_ws += 1

	# desk pages get the app icon in the sidebar / awesomebar
	for page, icon in (("rmc-live-dashboard", "rmc-dashboard"),
	                   ("rmc-control-tower", "rmc-dashboard"),
	                   ("rmc-batch-board", "rmc-batch"),
	                   ("rmc-dispatch-board", "rmc-dispatch"),
	                   ("rmc-silo-board", "rmc-silo"),
	                   ("rmc-quality-board", "rmc-quality"),
	                   ("rmc-guide", "rmc-guide")):
		if frappe.db.exists("Page", page) and frappe.get_meta("Page").has_field("icon"):
			frappe.db.set_value("Page", page, "icon", icon, update_modified=False)

	frappe.db.commit()
	frappe.clear_cache()
	print("  + icons: %d doctypes, %d workspaces" % (n_dt, n_ws))


run = install

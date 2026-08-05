"""Build the RMC app sidebars explicitly.

Frappe's auto-generator creates a Workspace Sidebar once and never revisits it,
so pages added later never appear. This owns the order and the icons instead —
one sidebar per workspace, each scoped to that job.
"""

import frappe

SIDEBARS = {
	"RMC Management": {
		"icon": "rmc-invoice",
		"items": [
			("Home", "Workspace", "RMC Management", "home"),
			("Management View", "Page", "rmc-manage", "rmc-invoice"),
			("Control Tower", "Page", "rmc-control-tower", "rmc-dashboard"),
			("Report Hub", "Page", "rmc-reports", "rmc-report"),
			("Monthly Plant Summary", "Report", "Monthly Plant Summary", "rmc-report"),
			("Grade Profitability", "Report", "Grade Profitability", "rmc-invoice"),
			("Customer Wise Sales", "Report", "Customer Wise Sales", "rmc-customer"),
			("Order Book", "Report", "Order Book and Pour Schedule", "rmc-order"),
			("Sales Invoice", "DocType", "Sales Invoice", "rmc-invoice"),
			("Purchase Receipt", "DocType", "Purchase Receipt", "rmc-inward"),
			("How to Use RMC", "Page", "rmc-guide", "rmc-guide"),
		],
	},
	"RMC Dashboard": {
		"icon": "rmc-dashboard",
		"items": [
			("Home", "Workspace", "RMC Dashboard", "home"),
			("Management", "Page", "rmc-manage", "rmc-invoice"),
			("Control Tower", "Page", "rmc-control-tower", "rmc-dashboard"),
			("Live Plant Dashboard", "Page", "rmc-live-dashboard", "rmc-status"),
			("Report Hub", "Page", "rmc-reports", "rmc-report"),
			("Production", "Workspace", "RMC Production", "rmc-batch"),
			("Materials", "Workspace", "RMC Materials", "rmc-silo"),
			("Dispatch", "Workspace", "RMC Dispatch", "rmc-dispatch"),
			("Quality", "Workspace", "RMC Quality", "rmc-quality"),
			("Setup", "Workspace", "RMC Setup", "rmc-settings"),
			("How to Use RMC", "Page", "rmc-guide", "rmc-guide"),
		],
	},
	"RMC Production": {
		"icon": "rmc-batch",
		"items": [
			("Home", "Workspace", "RMC Production", "home"),
			("Batching Board", "Page", "rmc-batch-board", "rmc-batch"),
			("Batch Production", "DocType", "Batch Production", "rmc-batch"),
			("Cube Test", "DocType", "Cube Test", "rmc-cube-test"),
			("Mix Design", "DocType", "Mix Design", "rmc-mix"),
			("Concrete Grade", "DocType", "Concrete Grade", "rmc-grade"),
			("Daily Production Summary", "Report", "Daily Production Summary", "rmc-report"),
			("Batch Register", "Report", "Batch Register", "rmc-batch"),
			("Consumption vs Recipe", "Report", "Material Consumption vs Recipe", "rmc-mix"),
			("Grade Profitability", "Report", "Grade Profitability", "rmc-invoice"),
			("Slump Compliance", "Report", "Slump Compliance", "rmc-slump"),
			("Stock Entry", "DocType", "Stock Entry", "rmc-stock"),
		],
	},
	"RMC Materials": {
		"icon": "rmc-silo",
		"items": [
			("Home", "Workspace", "RMC Materials", "home"),
			("Silo & Stock Board", "Page", "rmc-silo-board", "rmc-silo"),
			("Material Inward", "DocType", "Material Inward", "rmc-inward"),
			("Silo", "DocType", "Silo", "rmc-silo"),
			("Item", "DocType", "Item", "rmc-cement"),
			("Supplier", "DocType", "Supplier", "rmc-supplier"),
			("Purchase Receipt", "DocType", "Purchase Receipt", "rmc-inward"),
			("Stock Entry", "DocType", "Stock Entry", "rmc-stock"),
			("Material Inward Register", "Report", "Material Inward Register", "rmc-weighbridge"),
			("Silo and Stock Status", "Report", "Silo and Stock Status", "rmc-silo"),
			("Supplier Purchases", "Report", "Supplier Purchase Summary", "rmc-supplier"),
		],
	},
	"RMC Dispatch": {
		"icon": "rmc-dispatch",
		"items": [
			("Home", "Workspace", "RMC Dispatch", "home"),
			("Dispatch Board", "Page", "rmc-dispatch-board", "rmc-dispatch"),
			("Order 360", "Page", "rmc-order-360", "rmc-order"),
			("Concrete Order", "DocType", "Concrete Order", "rmc-order"),
			("Delivery Challan", "DocType", "Delivery Challan", "rmc-challan"),
			("Transit Mixer", "DocType", "Transit Mixer", "rmc-mixer"),
			("Driver", "DocType", "Driver", "rmc-driver"),
			("Construction Site", "DocType", "Construction Site", "rmc-site"),
			("Customer", "DocType", "Customer", "rmc-customer"),
			("Sales Invoice", "DocType", "Sales Invoice", "rmc-invoice"),
			("Dispatch Register", "Report", "Dispatch Register", "rmc-challan"),
			("Vehicle Utilisation", "Report", "Vehicle Utilisation and Trips", "rmc-cycle"),
			("Driver Performance", "Report", "Driver Performance", "rmc-driver"),
			("Order Book", "Report", "Order Book and Pour Schedule", "rmc-order"),
		],
	},
	"RMC Quality": {
		"icon": "rmc-quality",
		"items": [
			("Home", "Workspace", "RMC Quality", "home"),
			("Quality Board", "Page", "rmc-quality-board", "rmc-quality"),
			("Cube Test", "DocType", "Cube Test", "rmc-cube-test"),
			("Plant Status Log", "DocType", "Plant Status Log", "rmc-status"),
			("Breakdown Log", "DocType", "Breakdown Log", "rmc-breakdown"),
			("Maintenance", "DocType", "RMC Maintenance Task", "rmc-maintenance"),
			("Power Log", "DocType", "Power Log", "rmc-power"),
			("Cube Test Register", "Report", "Cube Test Register", "rmc-cube-test"),
			("Availability & Downtime", "Report", "Plant Availability and Downtime", "rmc-status"),
			("Power & Diesel", "Report", "Power and Diesel Consumption", "rmc-power"),
			("Monthly Summary", "Report", "Monthly Plant Summary", "rmc-report"),
		],
	},
	"RMC Setup": {
		"icon": "rmc-settings",
		"items": [
			("Home", "Workspace", "RMC Setup", "home"),
			("RMC Plant", "DocType", "RMC Plant", "rmc-plant"),
			("Concrete Grade", "DocType", "Concrete Grade", "rmc-grade"),
			("Mix Design", "DocType", "Mix Design", "rmc-mix"),
			("Silo", "DocType", "Silo", "rmc-silo"),
			("Transit Mixer", "DocType", "Transit Mixer", "rmc-mixer"),
			("Construction Site", "DocType", "Construction Site", "rmc-site"),
			("Customer", "DocType", "Customer", "rmc-customer"),
			("Supplier", "DocType", "Supplier", "rmc-supplier"),
			("RMC Settings", "DocType", "RMC Settings", "rmc-settings"),
			("How to Use RMC", "Page", "rmc-guide", "rmc-guide"),
		],
	},
}


def install():
	for name, cfg in SIDEBARS.items():
		if not frappe.db.exists("Workspace", name):
			continue
		if frappe.db.exists("Workspace Sidebar", name):
			doc = frappe.get_doc("Workspace Sidebar", name)
		else:
			doc = frappe.new_doc("Workspace Sidebar")
			doc.name = name
		doc.title = name
		doc.app = "rmc"
		doc.header_icon = cfg["icon"]
		doc.standard = 1
		doc.set("items", [])
		for label, link_type, link_to, icon in cfg["items"]:
			if not frappe.db.exists(link_type, link_to):
				continue
			doc.append("items", {"type": "Link", "label": label, "link_type": link_type,
			                     "link_to": link_to, "icon": icon})
		doc.flags.ignore_permissions = True
		doc.save()
	frappe.db.commit()
	frappe.clear_cache()
	print("  + sidebars: %d" % len(SIDEBARS))


run = install

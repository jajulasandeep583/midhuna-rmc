"""ERPNext core doctypes are extended, never forked.

Tagging the challan/plant onto the standard stock and sales documents is what
lets RMC numbers be read back out of the ledgers instead of kept in a parallel
accumulator.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install():
	create_custom_fields({
		"Sales Invoice": [{
			"fieldname": "rmc_delivery_challan",
			"label": "RMC Delivery Challan",
			"fieldtype": "Link",
			"options": "Delivery Challan",
			"insert_after": "po_no",
			"read_only": 1,
			"print_hide": 1,
			"no_copy": 1,
		}, {
			"fieldname": "rmc_construction_site",
			"label": "Construction Site",
			"fieldtype": "Link",
			"options": "Construction Site",
			"insert_after": "rmc_delivery_challan",
			"read_only": 1,
		}],
		"Stock Entry": [{
			"fieldname": "rmc_batch_production",
			"label": "RMC Batch Production",
			"fieldtype": "Link",
			"options": "Batch Production",
			"insert_after": "project",
			"read_only": 1,
			"no_copy": 1,
		}],
		"Purchase Receipt": [{
			"fieldname": "rmc_material_inward",
			"label": "RMC Material Inward",
			"fieldtype": "Link",
			"options": "Material Inward",
			"insert_after": "supplier_delivery_note",
			"read_only": 1,
			"no_copy": 1,
		}],
		"Customer": [{
			"fieldname": "rmc_credit_status",
			"label": "RMC Credit Status",
			"fieldtype": "Select",
			"options": "Normal\nWatch\nHold",
			"default": "Normal",
			"insert_after": "customer_group",
			"description": "Hold blocks new concrete orders for this customer.",
		}],
	}, ignore_validate=True)
	frappe.db.commit()
	print("  + custom fields on Sales Invoice / Stock Entry / Purchase Receipt / Customer")

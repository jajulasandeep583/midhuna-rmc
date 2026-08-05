"""Hooks fired by ERPNext core documents."""

import frappe


def on_sales_invoice_cancel(doc, method=None):
	"""Cancelling the invoice must not leave a challan pointing at a dead bill."""
	if not doc.get("rmc_delivery_challan"):
		return
	challan = doc.rmc_delivery_challan
	if frappe.db.exists("Delivery Challan", challan):
		frappe.db.set_value("Delivery Challan", challan, "sales_invoice", None,
		                    update_modified=False)

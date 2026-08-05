# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Concrete Order — what the customer booked, pour schedule included.

Delivered / pending quantities are never typed: they are recomputed from the
submitted Delivery Challans every time one is submitted or cancelled.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class ConcreteOrder(Document):
	def validate(self):
		if flt(self.order_qty_m3) <= 0:
			frappe.throw(_("Ordered Qty (m³) must be greater than zero."))
		if not flt(self.rate):
			self.rate = frappe.db.get_value("Concrete Grade", self.grade, "default_rate")
		self.order_value = flt(self.order_qty_m3) * flt(self.rate)

		if self.required_to and self.required_from and self.required_to < self.required_from:
			frappe.throw(_("Required To cannot be before Required From."))

		site_customer = frappe.db.get_value("Construction Site", self.construction_site, "customer")
		if site_customer and site_customer != self.customer:
			frappe.throw(_("Site {0} belongs to {1}, not {2}.").format(
				self.construction_site, site_customer, self.customer))

		if frappe.db.get_value("Customer", self.customer, "rmc_credit_status") == "Hold":
			frappe.throw(_("Customer {0} is on credit hold — order blocked.").format(self.customer))

		sched = sum(flt(r.qty_m3) for r in (self.schedule or []))
		if sched and sched > flt(self.order_qty_m3) + 0.001:
			frappe.throw(_("Scheduled quantity ({0} m³) exceeds the order quantity ({1} m³).")
			             .format(sched, self.order_qty_m3))

		if not flt(self.delivered_qty_m3):
			self.pending_qty_m3 = flt(self.order_qty_m3)

	def on_submit(self):
		self.db_set("status", "Open")

	def on_cancel(self):
		open_challans = frappe.get_all("Delivery Challan",
		                               filters={"concrete_order": self.name, "docstatus": 1},
		                               pluck="name")
		if open_challans:
			frappe.throw(_("Cancel the delivery challans first: {0}").format(
				", ".join(open_challans[:5])))
		self.db_set("status", "Cancelled")

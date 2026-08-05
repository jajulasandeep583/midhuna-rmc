# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Delivery Challan — the document that travels with every truck load.

On submit it does the three things an RMC plant needs to stay honest:
  * bills the load (Sales Invoice with update_stock, so the concrete leaves the
    finished-goods warehouse and revenue is booked in one step),
  * rolls the delivered quantity back onto the Concrete Order,
  * marks the transit mixer as on trip until the load is closed.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, time_diff_in_seconds, getdate


class DeliveryChallan(Document):
	def validate(self):
		self.set_defaults()
		self.compute_cycle_time()
		self.amount = flt(self.qty_m3) * flt(self.rate)
		if flt(self.qty_m3) <= 0:
			frappe.throw(_("Challan quantity must be greater than zero."))
		self.validate_against_order()

	def set_defaults(self):
		if self.concrete_order:
			order = frappe.db.get_value(
				"Concrete Order", self.concrete_order,
				["customer", "construction_site", "grade", "rate"], as_dict=True)
			if order:
				self.customer = self.customer or order.customer
				self.construction_site = self.construction_site or order.construction_site
				self.grade = self.grade or order.grade
				if not flt(self.rate):
					self.rate = order.rate
		if self.construction_site and not flt(self.distance_km):
			self.distance_km = frappe.db.get_value(
				"Construction Site", self.construction_site, "distance_km")
		if self.transit_mixer and not self.driver:
			self.driver = frappe.db.get_value("Transit Mixer", self.transit_mixer, "default_driver")
		if not self.qr_code:
			self.qr_code = "RMC|%s|%s|%s" % (self.name, self.grade, self.qty_m3)

	def compute_cycle_time(self):
		"""Dispatch → plant return, the core RMC productivity number."""
		if self.dispatch_time and self.return_time:
			mins = time_diff_in_seconds(self.return_time, self.dispatch_time) / 60.0
			self.cycle_time_min = cint(mins) if mins > 0 else 0
		else:
			self.cycle_time_min = 0

	def validate_against_order(self):
		"""A challan may not deliver more than the order has left — the single
		most common RMC billing dispute."""
		if not self.concrete_order:
			return
		order = frappe.get_doc("Concrete Order", self.concrete_order)
		if order.docstatus != 1:
			frappe.throw(_("Concrete Order {0} is not submitted.").format(self.concrete_order))
		if order.status == "Cancelled":
			frappe.throw(_("Concrete Order {0} is cancelled.").format(self.concrete_order))
		already = delivered_qty(self.concrete_order, exclude=self.name)
		if flt(already) + flt(self.qty_m3) > flt(order.order_qty_m3) + 0.001:
			frappe.throw(_(
				"Order {0} is for {1} m³; {2} m³ already delivered. This challan of {3} m³ "
				"would over-deliver by {4} m³."
			).format(self.concrete_order, order.order_qty_m3, already, self.qty_m3,
			         round(already + flt(self.qty_m3) - flt(order.order_qty_m3), 2)))

	def on_submit(self):
		if frappe.db.get_single_value("RMC Settings", "auto_create_sales_invoice"):
			self.make_sales_invoice()
		update_order_progress(self.concrete_order)
		if self.transit_mixer and self.status == "Dispatched":
			frappe.db.set_value("Transit Mixer", self.transit_mixer, "status", "On Trip")

	def on_update_after_submit(self):
		self.compute_cycle_time()
		self.db_set("cycle_time_min", self.cycle_time_min, update_modified=False)
		if self.status in ("Delivered", "Returned") and self.transit_mixer:
			frappe.db.set_value("Transit Mixer", self.transit_mixer, "status", "Available")

	def on_cancel(self):
		self.ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry",
		                               "Repost Item Valuation", "Serial and Batch Bundle")
		if self.sales_invoice:
			si = frappe.get_doc("Sales Invoice", self.sales_invoice)
			if si.docstatus == 1:
				si.flags.ignore_permissions = True
				si.cancel()
		self.db_set("status", "Cancelled")
		update_order_progress(self.concrete_order)
		if self.transit_mixer:
			frappe.db.set_value("Transit Mixer", self.transit_mixer, "status", "Available")

	# ------------------------------------------------------------------
	def make_sales_invoice(self):
		grade = frappe.get_doc("Concrete Grade", self.grade)
		plant_name = frappe.db.get_single_value("RMC Settings", "default_plant")
		plant = frappe.get_doc("RMC Plant", plant_name) if plant_name else None
		company = (plant.company if plant
		           else frappe.db.get_single_value("RMC Settings", "company")
		           or frappe.defaults.get_defaults().get("company"))

		si = frappe.new_doc("Sales Invoice")
		si.customer = self.customer
		si.company = company
		# A site set up without the ERPNext wizard has no default selling price
		# list, and Sales Invoice makes it mandatory — set it explicitly rather
		# than relying on Selling Settings.
		si.selling_price_list = (frappe.db.get_value("Price List",
		                                             {"selling": 1, "enabled": 1}, "name")
		                         or "Standard Selling")
		si.currency = frappe.db.get_value("Company", company, "default_currency") or "INR"
		si.price_list_currency = si.currency
		si.conversion_rate = 1
		si.plc_conversion_rate = 1
		si.posting_date = self.challan_date
		si.set_posting_time = 1
		# Bill at the moment the truck left, so the stock movement sits after the
		# batch that produced the load rather than at whatever time the clerk saved.
		if self.dispatch_time:
			si.posting_time = str(self.dispatch_time).split(" ")[-1]
		si.due_date = self.challan_date
		si.update_stock = 1
		si.rmc_delivery_challan = self.name
		si.rmc_construction_site = self.construction_site
		si.po_no = self.concrete_order
		si.append("items", {
			"item_code": grade.item_code,
			"qty": flt(self.qty_m3),
			"uom": "Cubic Meter",
			"rate": flt(self.rate),
			"warehouse": plant.finished_warehouse if plant else None,
			"description": "Ready Mix Concrete %s delivered at %s (Challan %s)"
			               % (self.grade, self.construction_site, self.name),
		})
		if plant and plant.cost_center:
			si.cost_center = plant.cost_center
			for row in si.items:
				row.cost_center = plant.cost_center
		si.flags.ignore_permissions = True
		si.insert()
		si.submit()
		self.db_set("sales_invoice", si.name)
		return si.name


def delivered_qty(order, exclude=None):
	if not order:
		return 0
	filters = {"concrete_order": order, "docstatus": 1}
	rows = frappe.get_all("Delivery Challan", filters=filters, fields=["name", "qty_m3"])
	return sum(flt(r.qty_m3) for r in rows if r.name != exclude)


def update_order_progress(order):
	"""Delivered / pending / status on the order are always derived, never typed."""
	if not order:
		return
	doc = frappe.get_doc("Concrete Order", order)
	delivered = delivered_qty(order)
	pending = flt(doc.order_qty_m3) - delivered
	if doc.status != "Cancelled":
		if delivered <= 0:
			status = "Open"
		elif pending > 0.001:
			status = "In Progress"
		else:
			status = "Completed"
		doc.db_set("status", status, update_modified=False)
	doc.db_set("delivered_qty_m3", delivered, update_modified=False)
	doc.db_set("pending_qty_m3", max(pending, 0), update_modified=False)

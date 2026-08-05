# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Material Inward — weighbridge receipt of cement, sand, aggregate, admixture.

Net weight comes off the weighbridge (gross − tare); on submit a standard
ERPNext Purchase Receipt posts the stock into that silo's warehouse and books
the supplier liability, so silo levels and payables are never a separate
spreadsheet.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

# Weighbridge tickets are in tonnes / kilolitres; stock is kept in kg / litre.
UNITS_PER_MT = 1000.0


class MaterialInward(Document):
	def validate(self):
		if flt(self.gross_weight) and flt(self.tare_weight):
			net = flt(self.gross_weight) - flt(self.tare_weight)
			if net <= 0:
				frappe.throw(_("Gross weight must exceed tare weight."))
			self.net_weight = net
		if flt(self.net_weight) <= 0:
			frappe.throw(_("Net weight must be greater than zero."))

		if self.silo:
			silo = frappe.db.get_value("Silo", self.silo,
			                           ["warehouse", "item_code", "material_type"], as_dict=True)
			self.warehouse = silo.warehouse
			if not self.item_code:
				self.item_code = silo.item_code
			if not self.material_type:
				self.material_type = silo.material_type
			if self.item_code != silo.item_code:
				frappe.throw(_("Silo {0} stores {1}, not {2}.").format(
					self.silo, silo.item_code, self.item_code))
		if not self.uom and self.item_code:
			self.uom = frappe.db.get_value("Item", self.item_code, "stock_uom")

		self.amount = flt(self.net_weight) * flt(self.rate)

	def on_submit(self):
		if not self.quality_ok:
			frappe.throw(_("Material failed quality check — it cannot be taken into stock. "
			               "Untick to record a rejection instead."))
		self.make_purchase_receipt()

	def on_cancel(self):
		self.ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry",
		                               "Repost Item Valuation", "Serial and Batch Bundle")
		if self.purchase_receipt:
			pr = frappe.get_doc("Purchase Receipt", self.purchase_receipt)
			if pr.docstatus == 1:
				pr.flags.ignore_permissions = True
				pr.cancel()

	# ------------------------------------------------------------------
	def make_purchase_receipt(self):
		plant = frappe.get_doc("RMC Plant", self.plant)
		qty = flt(self.net_weight) * UNITS_PER_MT
		rate = flt(self.amount) / qty if qty else 0

		pr = frappe.new_doc("Purchase Receipt")
		pr.supplier = self.supplier
		pr.company = plant.company
		pr.posting_date = self.inward_date
		pr.set_posting_time = 1
		pr.supplier_delivery_note = self.supplier_dc_no
		pr.rmc_material_inward = self.name
		pr.append("items", {
			"item_code": self.item_code,
			"qty": qty,
			"uom": frappe.db.get_value("Item", self.item_code, "stock_uom"),
			"stock_uom": frappe.db.get_value("Item", self.item_code, "stock_uom"),
			"conversion_factor": 1,
			"rate": rate,
			"warehouse": self.warehouse or plant.store_warehouse,
		})
		pr.flags.ignore_permissions = True
		pr.insert()
		pr.submit()
		self.db_set("purchase_receipt", pr.name)
		return pr.name

# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Batch Production — one batching run of concrete.

The document is the plant's own record (mix, shift, operator, target vs actual
consumption); the *stock* movement is a standard ERPNext Stock Entry of type
Manufacture created on submit, so raw material and finished concrete live in
the normal stock ledger and every ERPNext stock report just works.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class BatchProduction(Document):
	def validate(self):
		self.pull_recipe()
		self.compute_totals()
		if flt(self.qty_m3) <= 0:
			frappe.throw(_("Produced Qty (m³) must be greater than zero."))

	def pull_recipe(self):
		"""Fill the material grid from the mix design, and always keep the
		target column in step with qty × recipe."""
		if not self.mix_design:
			return
		design = frappe.get_doc("Mix Design", self.mix_design)
		if design.grade != self.grade:
			frappe.throw(_("Mix Design {0} is for grade {1}, not {2}.").format(
				self.mix_design, design.grade, self.grade))

		existing = {r.item_code: r for r in (self.materials or [])}
		rows = []
		for d in design.items:
			target = flt(d.qty_per_m3) * flt(self.qty_m3)
			row = existing.get(d.item_code)
			actual = flt(row.actual_qty) if row and flt(row.actual_qty) else target
			rate = flt(row.rate) if row and flt(row.rate) else flt(d.rate)
			rows.append({
				"item_code": d.item_code,
				"material_type": d.material_type,
				"target_qty": target,
				"actual_qty": actual,
				"uom": d.uom,
				"rate": rate,
				"amount": actual * rate,
				"variance_pct": (100.0 * (actual - target) / target) if target else 0,
				"warehouse": (row.warehouse if row and row.warehouse
				              else source_warehouse(d.item_code)),
			})
		self.set("materials", rows)

	def compute_totals(self):
		total = 0.0
		for r in self.materials or []:
			r.amount = flt(r.actual_qty) * flt(r.rate)
			r.variance_pct = ((100.0 * (flt(r.actual_qty) - flt(r.target_qty)) / flt(r.target_qty))
			                  if flt(r.target_qty) else 0)
			total += flt(r.amount)
		self.total_material_cost = total
		self.cost_per_m3 = total / flt(self.qty_m3) if flt(self.qty_m3) else 0

	def on_submit(self):
		if frappe.db.get_single_value("RMC Settings", "auto_stock_entry"):
			self.make_stock_entry()
		self.db_set("status", "Produced")

	def on_cancel(self):
		self.ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry",
		                               "Repost Item Valuation", "Serial and Batch Bundle")
		if self.stock_entry:
			se = frappe.get_doc("Stock Entry", self.stock_entry)
			if se.docstatus == 1:
				se.flags.ignore_permissions = True
				se.cancel()
		self.db_set("status", "Cancelled")

	# ------------------------------------------------------------------
	def make_stock_entry(self):
		"""Manufacture entry: raw materials out of their silos, concrete in."""
		plant = frappe.get_doc("RMC Plant", self.plant)
		grade = frappe.get_doc("Concrete Grade", self.grade)
		if not grade.item_code:
			frappe.throw(_("Concrete Grade {0} has no stock item.").format(self.grade))

		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Manufacture"
		se.purpose = "Manufacture"
		se.company = plant.company
		se.posting_date = self.production_date
		se.set_posting_time = 1
		if self.end_time:
			se.posting_time = str(self.end_time).split(" ")[-1]
		se.rmc_batch_production = self.name

		# NB: never set allow_zero_valuation_rate here. ERPNext reads that flag as
		# "value this line at zero", not "zero is acceptable if unknown" — it
		# silently posts the stock at 0, and every rupee of real cost then lands
		# in Stock Adjustment instead of Cost of Goods Sold, which quietly ruins
		# the P&L. Let the raw materials leave at their own moving-average
		# valuation and let ERPNext value the concrete from what it consumed.
		for r in self.materials or []:
			if flt(r.actual_qty) <= 0:
				continue
			se.append("items", {
				"item_code": r.item_code,
				"qty": flt(r.actual_qty),
				"s_warehouse": r.warehouse or source_warehouse(r.item_code) or plant.store_warehouse,
			})

		se.append("items", {
			"item_code": grade.item_code,
			"qty": flt(self.qty_m3),
			"t_warehouse": plant.finished_warehouse,
			"is_finished_item": 1,
		})

		if plant.cost_center:
			se.cost_center = plant.cost_center
			for row in se.items:
				row.cost_center = plant.cost_center

		se.flags.ignore_permissions = True
		se.insert()
		se.submit()
		self.db_set("stock_entry", se.name)
		return se.name


def source_warehouse(item_code):
	"""The silo / yard holding this item is its source warehouse."""
	return frappe.db.get_value("Silo", {"item_code": item_code, "is_active": 1}, "warehouse")

# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Mix Design — the per-m³ recipe every batch is measured against."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

# Total batched weight of one cubic metre of concrete. Anything far outside this
# band means a recipe was typed in the wrong unit.
MIN_KG_PER_M3 = 1800
MAX_KG_PER_M3 = 2800


class MixDesign(Document):
	def validate(self):
		if not self.items:
			frappe.throw(_("A mix design needs at least one material."))

		weight = 0.0
		cost = 0.0
		cement = 0.0
		water = 0.0
		for r in self.items:
			if flt(r.qty_per_m3) <= 0:
				frappe.throw(_("Qty per m³ must be greater than zero for {0}.").format(r.item_code))
			if not r.uom:
				r.uom = frappe.db.get_value("Item", r.item_code, "stock_uom")
			if not r.rate:
				r.rate = frappe.db.get_value("Item", r.item_code, "valuation_rate")
			r.amount = flt(r.qty_per_m3) * flt(r.rate)
			cost += r.amount
			# admixture is litres, everything else kg — only kg counts as weight
			if r.material_type != "Admixture":
				weight += flt(r.qty_per_m3)
			if r.material_type in ("Cement", "Fly Ash", "GGBS"):
				cement += flt(r.qty_per_m3)
			if r.material_type == "Water":
				water += flt(r.qty_per_m3)

		self.total_weight_kg = weight
		self.cost_per_m3 = cost
		if cement:
			self.water_cement_ratio = round(water / cement, 3)

		if not (MIN_KG_PER_M3 <= weight <= MAX_KG_PER_M3):
			frappe.msgprint(
				_("Batched weight is {0} kg/m³, outside the usual {1}–{2} kg/m³ band. "
				  "Check the quantities.").format(round(weight), MIN_KG_PER_M3, MAX_KG_PER_M3),
				indicator="orange", title=_("Unusual Mix"))

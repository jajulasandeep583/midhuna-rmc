# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Cube Test — compressive strength against the grade's design strength.

Pass/fail is derived, never typed: IS 456 accepts a 7-day cube at 65% of the
characteristic strength and a 28-day cube at 100%.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, add_days, getdate

# Fraction of the 28-day characteristic strength expected at each test age.
AGE_FACTOR = {7: 0.65, 14: 0.90, 28: 1.00}


class CubeTest(Document):
	def validate(self):
		if not self.grade and self.batch_production:
			self.grade = frappe.db.get_value("Batch Production", self.batch_production, "grade")
		if not self.casting_date and self.batch_production:
			self.casting_date = frappe.db.get_value(
				"Batch Production", self.batch_production, "production_date")

		age = cint(self.age_days)
		if not self.testing_date and self.casting_date:
			self.testing_date = add_days(getdate(self.casting_date), age)

		characteristic = flt(frappe.db.get_value("Concrete Grade", self.grade, "strength_mpa"))
		self.required_strength_mpa = characteristic * AGE_FACTOR.get(age, 1.0)

		if flt(self.avg_strength_mpa) <= 0:
			frappe.throw(_("Achieved strength must be greater than zero."))

		self.strength_pct = (100.0 * flt(self.avg_strength_mpa) / flt(self.required_strength_mpa)
		                     if flt(self.required_strength_mpa) else 0)
		self.result = "Pass" if flt(self.avg_strength_mpa) >= flt(self.required_strength_mpa) else "Fail"

	def on_submit(self):
		if self.result == "Fail":
			frappe.msgprint(
				_("Cube test {0} FAILED — {1} MPa against {2} MPa required for {3} at {4} days.")
				.format(self.name, self.avg_strength_mpa, round(self.required_strength_mpa, 1),
				        self.grade, self.age_days),
				title=_("Quality Alert"), indicator="red")

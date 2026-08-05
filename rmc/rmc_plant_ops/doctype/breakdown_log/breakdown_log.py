# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Breakdown Log — downtime hours are derived from the reported/resolved clock."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import time_diff_in_seconds


class BreakdownLog(Document):
	def validate(self):
		if self.resolved_on:
			secs = time_diff_in_seconds(self.resolved_on, self.reported_on)
			if secs < 0:
				frappe.throw(_("Resolved time cannot be before the reported time."))
			self.downtime_hours = round(secs / 3600.0, 2)
			if self.status != "Closed":
				self.status = "Closed"
		else:
			self.downtime_hours = 0
			if self.status == "Closed":
				frappe.throw(_("Set the resolved time before closing this breakdown."))

		if self.equipment == "Transit Mixer" and self.transit_mixer:
			target = "Under Maintenance" if self.status != "Closed" else "Available"
			frappe.db.set_value("Transit Mixer", self.transit_mixer, "status", target)

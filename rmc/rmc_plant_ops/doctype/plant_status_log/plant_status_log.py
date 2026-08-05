# Copyright (c) 2026, Midhuna Tech and contributors
# For license information, please see license.txt

"""Plant Status Log — the running / idle / breakdown clock behind availability %."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import time_diff_in_seconds


class PlantStatusLog(Document):
	def validate(self):
		if self.from_time and self.to_time:
			secs = time_diff_in_seconds(self.to_time, self.from_time)
			if secs <= 0:
				frappe.throw(_("'To' time must be after 'From' time."))
			self.duration_hours = round(secs / 3600.0, 2)
		if self.status in ("Breakdown", "Stopped") and not (self.reason or "").strip():
			frappe.throw(_("A reason is required when the plant is {0}.").format(self.status))

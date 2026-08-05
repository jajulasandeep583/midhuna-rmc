"""Scheduled housekeeping."""

import frappe
from frappe.utils import getdate, nowdate, flt


def refresh_order_status():
	"""Keep delivered/pending/status on every open order true to the challans."""
	from rmc.rmc_dispatch.doctype.delivery_challan.delivery_challan import update_order_progress

	for name in frappe.get_all("Concrete Order",
	                           filters={"docstatus": 1, "status": ["in", ["Open", "In Progress"]]},
	                           pluck="name"):
		try:
			update_order_progress(name)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "RMC: order refresh failed for %s" % name)
	frappe.db.commit()


def flag_due_maintenance():
	"""Move schedule rows into Due / Overdue as their date arrives."""
	today = getdate(nowdate())
	for row in frappe.get_all("RMC Maintenance Task",
	                          filters={"status": ["in", ["Scheduled", "Due"]]},
	                          fields=["name", "next_due_on", "status"]):
		if not row.next_due_on:
			continue
		due = getdate(row.next_due_on)
		target = "Overdue" if due < today else ("Due" if due == today else "Scheduled")
		if target != row.status:
			frappe.db.set_value("RMC Maintenance Task", row.name, "status", target,
			                    update_modified=False)
	frappe.db.commit()


def low_silos():
	"""Silos at or below their alert level — used by the dashboard and alerts."""
	out = []
	for s in frappe.get_all("Silo", filters={"is_active": 1},
	                        fields=["name", "silo_name", "item_code", "warehouse",
	                                "capacity_mt", "min_level_mt"]):
		qty = flt(frappe.db.get_value("Bin", {"item_code": s.item_code,
		                                      "warehouse": s.warehouse}, "actual_qty")) / 1000.0
		if s.min_level_mt and qty <= flt(s.min_level_mt):
			out.append({"silo": s.silo_name, "stock_mt": round(qty, 2),
			            "min_level": s.min_level_mt, "capacity": s.capacity_mt})
	return out

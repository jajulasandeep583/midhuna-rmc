__version__ = "1.0.0"

import frappe

RMC_ROLES = ("RMC Manager", "Plant Operator", "Dispatch Incharge",
             "Quality Engineer", "RMC Accounts")


def check_app_permission():
	"""Who sees the RMC tile on the /apps screen."""
	if frappe.session.user == "Administrator":
		return True
	roles = set(frappe.get_roles())
	return bool(roles & set(RMC_ROLES)) or "System Manager" in roles

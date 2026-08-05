"""Everything the RMC app builds for itself.

DocTypes, reports and workspaces are plain files in the app and are synced by
Frappe. What is NOT file-based — roles, masters, items, warehouses, silos,
number cards, charts, print formats — is built here, so a fresh
`bench install-app rmc` reproduces the whole product from this repository with
nothing done by hand.
"""

import frappe

ROLES = [
	"RMC Manager",
	"Plant Operator",
	"Dispatch Incharge",
	"Quality Engineer",
	"RMC Accounts",
]


def make_roles():
	for r in ROLES:
		if not frappe.db.exists("Role", r):
			frappe.get_doc({"doctype": "Role", "role_name": r, "desk_access": 1}).insert(
				ignore_permissions=True)
	print("  + roles: %d" % len(ROLES))


def after_install():
	print("Setting up RMC Plant Management...")
	make_roles()

	from rmc.setup import custom_fields, masters, workspaces, print_formats

	masters.install()
	custom_fields.install()
	print_formats.install()
	workspaces.install()

	frappe.db.commit()
	print("RMC Plant Management is ready. Open the RMC Plant workspace.")


def after_migrate():
	"""Keep desk objects in step with the code on every migrate."""
	from rmc.setup import custom_fields, print_formats, workspaces

	try:
		make_roles()
		custom_fields.install()
		print_formats.install()
		workspaces.install()
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "RMC: after_migrate rebuild failed")

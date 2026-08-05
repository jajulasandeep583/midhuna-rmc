"""Role permissions for the RMC doctypes, and the ERPNext roles each RMC role needs.

The doctypes are generated with permissions for System Manager, RMC Manager and
Plant Operator only. That leaves the Dispatch Incharge unable to open a
Delivery Challan and the Quality Engineer unable to record a cube test, so the
matrix is completed here.

Documents in the chain (Sales Invoice, Stock Entry, Purchase Receipt) belong to
ERPNext, whose permissions are role-based too — an RMC Manager who cannot open
the invoice their challan raised has a broken trail, so the matching ERPNext
roles are granted alongside.

    bench --site rmc.local execute rmc.setup.permissions.install
"""

import frappe

FULL = {"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1,
        "amend": 1, "report": 1, "export": 1, "print": 1, "email": 1, "share": 1}
WRITE = {"read": 1, "write": 1, "create": 1, "submit": 1, "report": 1, "print": 1,
         "share": 1, "email": 1}
READ = {"read": 1, "report": 1, "print": 1, "export": 1}

SETUP_DTS = ["RMC Plant", "Concrete Grade", "Mix Design", "Transit Mixer",
             "Construction Site", "Silo", "RMC Settings"]
PRODUCTION_DTS = ["Batch Production", "Cube Test"]
MATERIAL_DTS = ["Material Inward"]
DISPATCH_DTS = ["Concrete Order", "Delivery Challan"]
PLANT_DTS = ["Plant Status Log", "Breakdown Log", "RMC Maintenance Task", "Power Log"]

# role -> {level of access -> doctypes}
MATRIX = {
	"RMC Manager": {"full": SETUP_DTS + PRODUCTION_DTS + MATERIAL_DTS + DISPATCH_DTS + PLANT_DTS},
	"Plant Operator": {
		"write": PRODUCTION_DTS + MATERIAL_DTS + PLANT_DTS,
		"read": SETUP_DTS + DISPATCH_DTS,
	},
	"Dispatch Incharge": {
		"write": DISPATCH_DTS,
		"read": SETUP_DTS + PRODUCTION_DTS + PLANT_DTS,
	},
	"Quality Engineer": {
		"write": ["Cube Test", "Mix Design", "Breakdown Log", "Plant Status Log"],
		"read": SETUP_DTS + PRODUCTION_DTS + MATERIAL_DTS + DISPATCH_DTS + PLANT_DTS,
	},
	"RMC Accounts": {
		"read": SETUP_DTS + PRODUCTION_DTS + MATERIAL_DTS + DISPATCH_DTS + PLANT_DTS,
	},
}

# The ERPNext roles each RMC role needs so the document chain stays clickable.
ERPNEXT_ROLES = {
	"RMC Manager": ["Accounts Manager", "Stock Manager", "Purchase Manager",
	                "Sales Manager", "Item Manager"],
	"Plant Operator": ["Stock User", "Manufacturing User"],
	# Accounts User so the dispatcher can open the invoice their challan raised
	"Dispatch Incharge": ["Sales User", "Stock User", "Accounts User"],
	"Quality Engineer": ["Stock User", "Quality Manager"],
	"RMC Accounts": ["Accounts User", "Stock User", "Purchase User"],
}


def _perm_dict(level):
	return dict(FULL if level == "full" else WRITE if level == "write" else READ)


def install():
	"""Write the roles onto the DocTypes themselves.

	NOT Custom DocPerm: the moment one of those exists for a doctype, Frappe
	ignores the doctype's own permission rows entirely — which silently locked
	RMC Manager and Plant Operator out of everything the first time round.
	These are our own doctypes, so the rows belong on them (and in developer
	mode they land in the version-controlled JSON).
	"""
	# undo the Custom DocPerm approach if a previous run used it
	stale = frappe.get_all("Custom DocPerm",
	                       filters={"role": ["in", list(MATRIX.keys())]}, pluck="name")
	for name in stale:
		frappe.delete_doc("Custom DocPerm", name, force=True, ignore_permissions=True)

	wanted = {}          # doctype -> {role: perms}
	for role, levels in MATRIX.items():
		if not frappe.db.exists("Role", role):
			continue
		for level, doctypes in levels.items():
			for dt in doctypes:
				wanted.setdefault(dt, {})
				# a role listed twice keeps the wider grant
				if level == "full" or role not in wanted[dt]:
					wanted[dt][role] = level

	touched = 0
	for dt, roles in wanted.items():
		if not frappe.db.exists("DocType", dt):
			continue
		doc = frappe.get_doc("DocType", dt)
		have = {p.role for p in doc.permissions}
		added = False
		for role, level in roles.items():
			if role in have:
				continue
			perms = _perm_dict(level)
			if not doc.is_submittable:
				for k in ("submit", "cancel", "amend"):
					perms.pop(k, None)
			doc.append("permissions", {"role": role, "permlevel": 0, **perms})
			added = True
			touched += 1
		if added:
			doc.flags.ignore_permissions = True
			doc.save()

	frappe.clear_cache()
	frappe.db.commit()
	print("  + doctype permission rows added: %d (stale Custom DocPerms removed: %d)"
	      % (touched, len(stale)))


def grant_erpnext_roles():
	"""Give every user holding an RMC role the ERPNext roles that role implies."""
	n = 0
	for rmc_role, erp_roles in ERPNEXT_ROLES.items():
		users = frappe.get_all("Has Role", filters={"role": rmc_role, "parenttype": "User"},
		                       pluck="parent")
		for user in set(users):
			if user in ("Administrator", "Guest") or not frappe.db.exists("User", user):
				continue
			doc = frappe.get_doc("User", user)
			have = {r.role for r in doc.roles}
			added = False
			for r in erp_roles:
				if frappe.db.exists("Role", r) and r not in have:
					doc.append("roles", {"role": r})
					added = True
			if added:
				doc.flags.ignore_permissions = True
				doc.save()
				n += 1
	frappe.db.commit()
	print("  + users granted matching ERPNext roles: %d" % n)


def run():
	install()
	grant_erpnext_roles()

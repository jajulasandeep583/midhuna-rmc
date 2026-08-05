"""The five role logins used to demo the plant.

    bench --site rmc.local execute rmc.setup.demo_users.install

Password is the same for all of them; change it before anything goes live.
"""

import frappe
from frappe.utils.password import update_password

PASSWORD = "Demo@12345"

USERS = [
	("manager@midhunarmc.com", "Ravi", "Kumar", "Plant Manager",
	 ["RMC Manager", "System Manager"]),
	("operator@midhunarmc.com", "Srinivas", "K", "Batching Operator", ["Plant Operator"]),
	("dispatch@midhunarmc.com", "Prasad", "Babu", "Dispatch Incharge", ["Dispatch Incharge"]),
	("quality@midhunarmc.com", "Lakshmi", "Prasanna", "Quality Engineer", ["Quality Engineer"]),
	("accounts@midhunarmc.com", "Anil", "M", "Accounts", ["RMC Accounts"]),
]


def install():
	for email, first, last, designation, roles in USERS:
		if frappe.db.exists("User", email):
			user = frappe.get_doc("User", email)
		else:
			user = frappe.get_doc({
				"doctype": "User", "email": email, "first_name": first, "last_name": last,
				"send_welcome_email": 0, "user_type": "System User",
			})
			user.flags.ignore_permissions = True
			user.insert()
		user.enabled = 1
		user.designation = designation
		have = {r.role for r in user.roles}
		for r in roles:
			if frappe.db.exists("Role", r) and r not in have:
				user.append("roles", {"role": r})
		user.flags.ignore_permissions = True
		user.save()
		update_password(email, PASSWORD)

	frappe.db.commit()

	from rmc.setup import permissions
	permissions.grant_erpnext_roles()

	from frappe.auth import check_password
	ok = 0
	for email, *_ in USERS:
		try:
			check_password(email, PASSWORD)
			ok += 1
		except Exception:
			print("  ! login FAILED for %s" % email)
	print("  + demo users: %d of %d authenticate" % (ok, len(USERS)))

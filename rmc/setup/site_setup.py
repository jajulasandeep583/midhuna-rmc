"""Finish the ERPNext setup wizard and fill the site's master data properly.

The site was created head-less (no wizard), which leaves it usable but bare:
the wizard banner keeps nagging, the company carries no address or tax id, and
customers, suppliers and items have no contact, address, GST or HSN details.

This completes the wizard for frappe + erpnext and fills all of that in for
**Midhuna RMC**. Idempotent.

    bench --site rmc.local execute rmc.setup.site_setup.run
"""

import frappe
from frappe.utils import flt

COMPANY = "Midhuna RMC"

COMPANY_PROFILE = {
	"phone_no": "+91 83418 63917",
	"email": "info@midhunacontrols.com",
	"website": "https://www.midhunatech.net",
	"tax_id": "37AAMCM1234K1ZP",              # GSTIN
	"date_of_establishment": "2024-04-01",
	"country": "India",
	"default_currency": "INR",
	"domain": "Manufacturing",
	"company_description": (
		"Midhuna RMC operates a 60 m³/hr ready mix concrete plant at Visakhapatnam, "
		"supplying M10 to M60 grade concrete to construction sites across the district. "
		"Plant operations run on the Midhunatech RMC Plant Smart ERP."
	),
}

COMPANY_ADDRESS = {
	"address_line1": "Survey No. 214/2, NH-16 Service Road",
	"address_line2": "Sabbavaram Mandal, Anakapalle District",
	"city": "Visakhapatnam",
	"state": "Andhra Pradesh",
	"pincode": "531035",
	"country": "India",
}

# Customer details: (name, GSTIN, credit limit, city, pincode, contact, phone)
CUSTOMER_DETAILS = {
	"Sri Venkateswara Constructions Pvt Ltd":
		("37AABCS4521M1Z8", 5000000, "Visakhapatnam", "530016",
		 "Ravi Teja", "9885012345", "Beach Road, MVP Colony"),
	"Coastal Infra Projects Ltd":
		("37AACCC8834L1ZQ", 8000000, "Visakhapatnam", "530003",
		 "Naveen Chandra", "9885023456", "Dwaraka Nagar, Main Road"),
	"Gayatri Builders and Developers":
		("37AAFCG2290P1ZR", 3000000, "Visakhapatnam", "530040",
		 "Suresh Varma", "9885034567", "Madhurawada, Sector 5"),
	"NCC Infrastructure Ltd":
		("37AAACN1234F1ZT", 12000000, "Anakapalle", "531001",
		 "Kiran Kumar", "9885045678", "Flyover Package Site Office"),
	"Ramky Housing Pvt Ltd":
		("37AAGCR5567H1ZV", 6000000, "Visakhapatnam", "530045",
		 "Anil Reddy", "9885056789", "Kommadi Junction"),
	"Sagar Cements Township Project":
		("37AABCS9912K1ZW", 4000000, "Bheemili", "531163",
		 "Prakash Rao", "9885067890", "Township Site, Bheemili Road"),
	"APSRTC Depot Works":
		("37AAAGA0012C1ZX", 2500000, "Gajuwaka", "530026",
		 "Depot Engineer", "9885078901", "RTC Depot, Gajuwaka"),
	"Vizag Port Trust Works":
		("37AAAJV0034D1ZY", 15000000, "Visakhapatnam", "530035",
		 "Berth Engineer", "9885089012", "Berth 8, Inner Harbour"),
}

# Supplier details: (GSTIN, city, contact, phone)
SUPPLIER_DETAILS = {
	"Ultratech Cement Ltd": ("36AAACL6442L1ZM", "Hyderabad", "Sales Desk", "9848011111"),
	"Sagar Cements Ltd": ("36AAACS4644Q1ZK", "Hyderabad", "Depot Manager", "9848022222"),
	"Godavari Sand Suppliers": ("37AAJFG7712N1ZB", "Rajahmundry", "Ch. Ramesh", "9848033333"),
	"Vizag Aggregates and Metals": ("37AAKFV3390R1ZC", "Visakhapatnam", "M. Suresh", "9848044444"),
	"NTPC Fly Ash Depot": ("37AAACN0255D1ZE", "Visakhapatnam", "Ash Cell", "9848055555"),
	"Fosroc Chemicals India": ("29AAACF5678G1ZF", "Bengaluru", "Technical Sales", "9848066666"),
	"JSW Slag Products": ("37AAACJ4045P1ZH", "Visakhapatnam", "GGBS Desk", "9848077777"),
	"Vizag Municipal Water Tankers": ("37AAALV0091J1ZJ", "Visakhapatnam", "Water Cell", "9848088888"),
}

# HSN codes — what an Indian RMC plant actually bills under
HSN = {
	"RM-CEM-OPC53": "25232910", "RM-CEM-PPC": "25232930", "RM-FLYASH": "26219000",
	"RM-GGBS": "26180000", "RM-SAND": "25051019", "RM-MSAND": "25171010",
	"RM-AGG20": "25171010", "RM-AGG10": "25171010", "RM-ADMIX": "38244010",
	"RM-WATER": "22011010",
}
CONCRETE_HSN = "38245010"          # ready-mix concrete


def _complete_wizard():
	"""Mark the wizard done for frappe and erpnext so the banner stops."""
	# rmc is included deliberately: it ships no setup wizard of its own, and
	# frappe hides an app's tile on the /apps screen from anyone without System
	# Manager until that app is flagged complete — which would leave the
	# operator, dispatch and quality logins staring at a desk with no RMC tile.
	for app in ("frappe", "erpnext", "rmc"):
		if frappe.db.exists("Installed Application", {"app_name": app}):
			frappe.db.set_value("Installed Application", {"app_name": app},
			                    "is_setup_complete", 1)
	# Set the flag ON the document, not with a separate db write: a later
	# settings.save() reloads the cached single and writes the stale 0 straight
	# back, which leaves the desk bouncing every login into the setup wizard.
	settings = frappe.get_single("System Settings")
	settings.setup_complete = 1
	settings.country = "India"
	settings.time_zone = "Asia/Kolkata"
	settings.currency = "INR"
	settings.language = "en"
	settings.date_format = "dd-mm-yyyy"
	settings.time_format = "HH:mm:ss"
	settings.number_format = "#,###.##"
	settings.float_precision = 3
	settings.currency_precision = 2
	settings.first_day_of_the_week = "Monday"
	settings.flags.ignore_mandatory = True
	settings.save(ignore_permissions=True)

	frappe.db.set_default("company", COMPANY)
	frappe.db.set_default("country", "India")
	frappe.db.set_default("currency", "INR")

	# THE one that actually keeps users out of the desk: a fresh site is created
	# with desktop:home_page = "setup-wizard", and only the wizard's completion
	# step clears it. Boot then hands the browser home_page "setup-wizard", the
	# wizard page redirects to /desk without stopping its own load, and the two
	# bounce off each other — which looks exactly like the site failing to open.
	frappe.db.set_default("desktop:home_page", "workspace")
	frappe.db.set_default("setup_complete", "1")

	frappe.db.commit()
	frappe.clear_cache()          # boot info caches setup_complete

	check = frappe.db.get_single_value("System Settings", "setup_complete")
	print("  + setup wizard marked complete (frappe, erpnext, rmc); "
	      "System Settings.setup_complete = %s" % check)


def _company_profile():
	doc = frappe.get_doc("Company", COMPANY)
	for k, v in COMPANY_PROFILE.items():
		if doc.meta.has_field(k):
			doc.set(k, v)
	doc.flags.ignore_permissions = True
	doc.save()
	_address("Company", COMPANY, COMPANY + " - Plant", COMPANY_ADDRESS,
	         COMPANY_PROFILE["phone_no"], COMPANY_PROFILE["email"], is_company=True)
	print("  + company profile: address, GSTIN, contact, description")


def _address(dt, dn, title, addr, phone=None, email=None, is_company=False):
	name = "%s-%s" % (title, "Billing")
	if frappe.db.exists("Address", {"address_title": title}):
		return
	doc = frappe.get_doc({
		"doctype": "Address", "address_title": title,
		"address_type": "Billing",
		"address_line1": addr["address_line1"],
		"address_line2": addr.get("address_line2"),
		"city": addr["city"], "state": addr.get("state", "Andhra Pradesh"),
		"pincode": addr.get("pincode"), "country": addr.get("country", "India"),
		"phone": phone, "email_id": email,
		"is_primary_address": 1, "is_shipping_address": 1,
		"links": [{"link_doctype": dt, "link_name": dn}],
	})
	doc.flags.ignore_permissions = True
	doc.insert()


def _contact(dt, dn, person, phone, email=None, designation=None):
	first = person.split(" ")[0]
	last = " ".join(person.split(" ")[1:]) or None
	if frappe.db.exists("Contact", {"first_name": first, "last_name": last,
	                                "phone": phone}):
		return
	doc = frappe.get_doc({
		"doctype": "Contact", "first_name": first, "last_name": last,
		"designation": designation, "is_primary_contact": 1,
		"links": [{"link_doctype": dt, "link_name": dn}],
	})
	if phone:
		doc.append("phone_nos", {"phone": phone, "is_primary_mobile_no": 1,
		                         "is_primary_phone": 1})
	if email:
		doc.append("email_ids", {"email_id": email, "is_primary": 1})
	doc.flags.ignore_permissions = True
	doc.insert()


def _customers():
	n = 0
	for cust, (gstin, limit, city, pin, person, phone, line1) in CUSTOMER_DETAILS.items():
		if not frappe.db.exists("Customer", cust):
			continue
		doc = frappe.get_doc("Customer", cust)
		doc.tax_id = gstin
		if doc.meta.has_field("gstin"):
			doc.gstin = gstin
		doc.customer_type = "Company"
		# these masters only exist if the relevant ERPNext fixtures were loaded
		doc.tax_category = _ensure("Tax Category", "In-State", {"title": "In-State"})
		doc.industry = _ensure("Industry Type", "Real Estate", {"industry": "Real Estate"})
		doc.market_segment = _ensure("Market Segment", "Enterprise",
		                             {"market_segment": "Enterprise"})
		doc.default_currency = "INR"
		doc.payment_terms = _payment_terms()
		doc.language = "en"
		if not doc.get("credit_limits"):
			doc.append("credit_limits", {"company": COMPANY, "credit_limit": limit,
			                             "bypass_credit_limit_check": 0})
		doc.flags.ignore_permissions = True
		doc.save()
		_address("Customer", cust, cust,
		         {"address_line1": line1, "city": city, "pincode": pin,
		          "state": "Andhra Pradesh", "country": "India"}, phone)
		_contact("Customer", cust, person, phone,
		         designation="Site Engineer")
		n += 1
	print("  + customers enriched: %d (GSTIN, credit limit, address, contact)" % n)


def _suppliers():
	n = 0
	for supp, (gstin, city, person, phone) in SUPPLIER_DETAILS.items():
		if not frappe.db.exists("Supplier", supp):
			continue
		doc = frappe.get_doc("Supplier", supp)
		doc.tax_id = gstin
		if doc.meta.has_field("gstin"):
			doc.gstin = gstin
		doc.supplier_type = "Company"
		doc.country = "India"
		doc.default_currency = "INR"
		doc.payment_terms = _payment_terms()
		doc.flags.ignore_permissions = True
		doc.save()
		_address("Supplier", supp, supp,
		         {"address_line1": "%s Works" % supp, "city": city,
		          "state": "Andhra Pradesh", "country": "India"}, phone)
		_contact("Supplier", supp, person, phone, designation="Sales")
		n += 1
	print("  + suppliers enriched: %d (GSTIN, address, contact)" % n)


def _ensure(doctype, name, payload):
	"""Create a small master if the site does not have it, and return its name.

	A head-less site carries only the fixtures ERPNext seeds, so optional
	masters like Tax Category or Market Segment may simply not be there.
	"""
	if frappe.db.exists(doctype, name):
		return name
	try:
		doc = frappe.get_doc({"doctype": doctype, **payload})
		doc.flags.ignore_permissions = True
		doc.insert(ignore_if_duplicate=True)
		return doc.name
	except Exception:
		frappe.log_error(frappe.get_traceback(), "RMC: could not create %s %s" % (doctype, name))
		return None


def _payment_terms():
	"""A 30-day credit template, the RMC industry norm."""
	name = "30 Days Credit"
	if not frappe.db.exists("Payment Term", name):
		frappe.get_doc({"doctype": "Payment Term", "payment_term_name": name,
		                "due_date_based_on": "Day(s) after invoice date",
		                "credit_days": 30, "invoice_portion": 100
		                }).insert(ignore_permissions=True)
	if not frappe.db.exists("Payment Terms Template", name):
		frappe.get_doc({
			"doctype": "Payment Terms Template", "template_name": name,
			"terms": [{"payment_term": name, "due_date_based_on": "Day(s) after invoice date",
			           "credit_days": 30, "invoice_portion": 100}],
		}).insert(ignore_permissions=True)
	return name


def _hsn_field():
	"""Somewhere to keep the HSN code.

	india_compliance would add `gst_hsn_code`, but it is not installed here and
	bolting it onto a site that already carries a month of posted invoices is
	not worth the risk — so the app keeps its own field, and uses the GST one
	instead whenever that app IS present.
	"""
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	if frappe.get_meta("Item").has_field("gst_hsn_code"):
		return "gst_hsn_code"
	create_custom_fields({
		"Item": [{
			"fieldname": "rmc_hsn_code", "label": "HSN / SAC Code", "fieldtype": "Data",
			"insert_after": "item_group", "description": "Printed on GST invoices.",
		}]
	}, ignore_validate=True)
	return "rmc_hsn_code"


def _items():
	"""HSN codes, brands, descriptions and reorder levels on every item."""
	from rmc.setup.masters import GRADES

	hsn_field = _hsn_field()
	n = 0
	for code, hsn in HSN.items():
		if not frappe.db.exists("Item", code):
			continue
		doc = frappe.get_doc("Item", code)
		doc.set(hsn_field, hsn)
		doc.description = doc.description or doc.item_name
		doc.item_group = doc.item_group or "RMC Raw Material"
		silo = frappe.db.get_value("Silo", {"item_code": code},
		                           ["warehouse", "capacity_mt", "min_level_mt"], as_dict=True)
		if silo and not doc.get("reorder_levels"):
			doc.append("reorder_levels", {
				"warehouse": silo.warehouse,
				"warehouse_reorder_level": flt(silo.min_level_mt) * 1000,
				"warehouse_reorder_qty": flt(silo.capacity_mt) * 1000 * 0.5,
				"material_request_type": "Purchase",
			})
		doc.flags.ignore_permissions = True
		doc.save()
		n += 1

	for grade, mpa, application, rate in GRADES:
		code = "RMC-%s" % grade
		if not frappe.db.exists("Item", code):
			continue
		doc = frappe.get_doc("Item", code)
		doc.set(hsn_field, CONCRETE_HSN)
		doc.description = ("Ready mix concrete of grade %s — characteristic compressive "
		                   "strength %d MPa at 28 days. Typical use: %s."
		                   % (grade, mpa, application))
		doc.brand = _brand()
		doc.flags.ignore_permissions = True
		doc.save()
		_item_price(code, rate)
		n += 1
	print("  + items enriched: %d (HSN, description, reorder level, selling price)" % n)


def _brand():
	if not frappe.db.exists("Brand", "Midhuna RMC"):
		frappe.get_doc({"doctype": "Brand", "brand": "Midhuna RMC",
		                "description": "Ready mix concrete produced at the Midhuna RMC plant."
		                }).insert(ignore_permissions=True)
	return "Midhuna RMC"


def _item_price(item_code, rate):
	if frappe.db.exists("Item Price", {"item_code": item_code,
	                                   "price_list": "Standard Selling"}):
		return
	frappe.get_doc({
		"doctype": "Item Price", "item_code": item_code, "price_list": "Standard Selling",
		"selling": 1, "price_list_rate": rate, "currency": "INR",
	}).insert(ignore_permissions=True)


def _defaults():
	"""Selling / Buying / Stock settings so new documents come up pre-filled."""
	s = frappe.get_single("Selling Settings")
	s.selling_price_list = "Standard Selling"
	s.cust_master_name = "Customer Name"
	s.so_required = "No"
	s.dn_required = "No"
	s.flags.ignore_mandatory = True
	s.save(ignore_permissions=True)

	b = frappe.get_single("Buying Settings")
	b.buying_price_list = "Standard Buying"
	b.supp_master_name = "Supplier Name"
	b.po_required = "No"
	b.pr_required = "No"
	b.flags.ignore_mandatory = True
	b.save(ignore_permissions=True)

	st = frappe.get_single("Stock Settings")
	st.item_naming_by = "Item Code"
	st.allow_negative_stock = 0
	# valuation method is deliberately left as-is: ERPNext refuses to change it
	# once stock transactions exist, and this site already has a month of them
	st.flags.ignore_mandatory = True
	st.save(ignore_permissions=True)

	plant = frappe.db.get_single_value("RMC Settings", "default_plant")
	if plant:
		frappe.db.set_value("RMC Plant", plant, "cost_center",
		                    frappe.db.get_value("Cost Center",
		                                        {"company": COMPANY, "is_group": 0}, "name"))
	print("  + selling / buying / stock defaults set")


def run():
	print("Completing site setup for %s..." % COMPANY)
	_complete_wizard()
	_company_profile()
	_payment_terms()
	_customers()
	_suppliers()
	_items()
	_defaults()
	frappe.db.commit()
	print("Site setup complete.")

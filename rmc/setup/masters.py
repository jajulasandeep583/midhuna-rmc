"""Company, warehouses, items, grades, mix designs, plant and silos.

Everything an RMC plant needs before the first pour. Idempotent — safe to
re-run; existing records are updated, never duplicated.

    bench --site rmc.local execute rmc.setup.masters.install
"""

import frappe

COMPANY_NAME = "Midhuna RMC"
COMPANY_ABBR = "MRMC"
PLANT_NAME = "Midhuna RMC Plant - Visakhapatnam"

# (grade, MPa, application, ₹/m³)
GRADES = [
	("M10", 10, "PCC / levelling course", 4200),
	("M15", 15, "Flooring, kerbs, non-structural", 4450),
	("M20", 20, "Residential slabs, footings", 4800),
	("M25", 25, "RCC slabs, columns, beams", 5150),
	("M30", 30, "High-rise structural, water tanks", 5500),
	("M35", 35, "Bridges, industrial floors", 5850),
	("M40", 40, "Pre-stressed, heavy structural", 6300),
	("M50", 50, "Piers, high-rise cores", 7100),
	("M60", 60, "Special structural, high performance", 8200),
]

# (item_code, item_name, material_type, uom, rate, is_stock)
RAW_MATERIALS = [
	("RM-CEM-OPC53", "OPC 53 Grade Cement", "Cement", "Kg", 6.80),
	("RM-CEM-PPC", "PPC Cement", "Cement", "Kg", 6.20),
	("RM-FLYASH", "Fly Ash", "Fly Ash", "Kg", 2.10),
	("RM-GGBS", "GGBS", "GGBS", "Kg", 3.40),
	("RM-SAND", "River Sand (Fine Aggregate)", "Sand", "Kg", 1.35),
	("RM-MSAND", "M-Sand", "Sand", "Kg", 1.10),
	("RM-AGG20", "Coarse Aggregate 20mm", "Aggregate", "Kg", 0.95),
	("RM-AGG10", "Coarse Aggregate 10mm", "Aggregate", "Kg", 1.05),
	("RM-ADMIX", "Superplasticiser Admixture", "Admixture", "Litre", 78.00),
	("RM-WATER", "Water", "Water", "Litre", 0.08),
]

# Silos / yards: (name, material_type, item, capacity)
SILOS = [
	("Cement Silo 1", "Cement", "RM-CEM-OPC53", 100),
	("Cement Silo 2", "Cement", "RM-CEM-PPC", 100),
	("Fly Ash Silo", "Fly Ash", "RM-FLYASH", 80),
	("GGBS Silo", "GGBS", "RM-GGBS", 80),
	("Sand Yard", "Sand", "RM-SAND", 600),
	("M-Sand Yard", "Sand", "RM-MSAND", 400),
	("Aggregate Yard 20mm", "Aggregate", "RM-AGG20", 800),
	("Aggregate Yard 10mm", "Aggregate", "RM-AGG10", 500),
	# Liquids turn over far faster than the solids (a 60 m³/hr plant draws
	# ~150 L of water per m³), so their tanks are sized for several days of
	# batching, not one.
	("Admixture Tank", "Admixture", "RM-ADMIX", 40),
	("Water Tank", "Water", "RM-WATER", 150),
]

# Mix designs per m³ (kg, except admixture=litre, water=litre).
# Cement content rises and w/c falls as the grade goes up — the standard IS
# 10262 shape, rounded to what a plant actually batches.
MIX = {
	#        cement, flyash, sand, agg20, agg10, admix, water, w/c
	"M10": (200, 0, 780, 720, 480, 1.4, 150, 0.75),
	"M15": (240, 0, 760, 730, 480, 1.8, 148, 0.62),
	"M20": (280, 40, 730, 740, 490, 2.4, 145, 0.52),
	"M25": (310, 60, 700, 745, 495, 3.0, 143, 0.46),
	"M30": (340, 70, 680, 750, 500, 3.6, 140, 0.41),
	"M35": (370, 80, 660, 755, 500, 4.2, 138, 0.37),
	"M40": (400, 90, 640, 760, 505, 4.8, 136, 0.34),
	"M50": (440, 110, 610, 765, 510, 5.6, 132, 0.30),
	"M60": (480, 130, 580, 770, 515, 6.5, 128, 0.27),
}

WAREHOUSES = [
	# (warehouse name, is_group, parent)
	("RMC Plant Store", 1, None),
	("Finished Concrete", 0, None),
]


def _erpnext_fixtures():
	"""Seed the standard ERPNext roots (item groups, customer groups, territories,
	UOMs, warehouse types...).

	The site was created without running the setup wizard, so none of them exist
	and every master insert below would fail on link validation. This is exactly
	what the wizard's first step does.
	"""
	if frappe.db.exists("Item Group", "All Item Groups"):
		return

	# frappe.locale.get_locale_value() reads an unbound local when System Settings
	# carries no language — which is the state of a site created without the
	# wizard. Anything that formats a date during the fixture install trips it,
	# so set the locale defaults first.
	settings = frappe.get_single("System Settings")
	settings.language = settings.language or "en"
	settings.country = settings.country or "India"
	settings.time_zone = settings.time_zone or "Asia/Kolkata"
	settings.currency = settings.currency or "INR"
	settings.date_format = settings.date_format or "dd-mm-yyyy"
	settings.flags.ignore_mandatory = True
	settings.save(ignore_permissions=True)
	frappe.db.commit()
	frappe.clear_cache()

	from erpnext.setup.setup_wizard.operations.install_fixtures import install as erp_install
	erp_install("India")
	frappe.db.commit()


def _company():
	name = frappe.db.get_value("Company", {"company_name": COMPANY_NAME}, "name")
	if name:
		return name
	name = frappe.db.get_value("Company", {}, "name")
	if name:
		return name
	# Company creation makes standard warehouses and departments that need roots
	# the ERPNext setup wizard would have seeded. This site was created without
	# running the wizard, so seed them here or the insert fails on link validation.
	if not frappe.db.exists("Warehouse Type", "Transit"):
		frappe.get_doc({"doctype": "Warehouse Type", "name": "Transit"}).insert(
			ignore_permissions=True, ignore_if_duplicate=True)
	if not frappe.db.exists("Department", "All Departments"):
		# ERPNext creates this root itself during company setup, but its record
		# omits `company`, which is mandatory in v16 — the insert fails and every
		# child department then dies on a missing parent. Seed the root here with
		# mandatory checks off (a tree root legitimately has no company).
		root = frappe.get_doc({"doctype": "Department", "department_name": "All Departments",
		                       "is_group": 1, "parent_department": ""})
		root.flags.ignore_mandatory = True
		root.insert(ignore_permissions=True, ignore_if_duplicate=True)
	doc = frappe.get_doc({
		"doctype": "Company",
		"company_name": COMPANY_NAME,
		"abbr": COMPANY_ABBR,
		"default_currency": "INR",
		"country": "India",
		"create_chart_of_accounts_based_on": "Standard Template",
		"chart_of_accounts": "Standard",
	}).insert(ignore_permissions=True)
	frappe.db.set_default("company", doc.name)
	return doc.name


def _fiscal_year():
	from frappe.utils import getdate

	# ERPNext ships a "Notification for new fiscal year" whose Jinja template
	# raises on this build; it fires on Fiscal Year insert and would abort the
	# whole setup. It is pure e-mail noise on a plant site — switch it off.
	broken = "Notification for new fiscal year"
	if frappe.db.exists("Notification", broken):
		frappe.db.set_value("Notification", broken, "enabled", 0)

	today = getdate()
	start_year = today.year if today.month >= 4 else today.year - 1
	fy = "%d-%d" % (start_year, start_year + 1)
	if not frappe.db.exists("Fiscal Year", fy):
		frappe.get_doc({
			"doctype": "Fiscal Year", "year": fy,
			"year_start_date": "%d-04-01" % start_year,
			"year_end_date": "%d-03-31" % (start_year + 1),
		}).insert(ignore_permissions=True)
	return fy


def _abbr(company):
	return frappe.db.get_value("Company", company, "abbr")


def _warehouse(name, company, is_group=0, parent=None):
	abbr = _abbr(company)
	full = "%s - %s" % (name, abbr)
	if frappe.db.exists("Warehouse", full):
		return full
	doc = frappe.get_doc({
		"doctype": "Warehouse", "warehouse_name": name, "company": company,
		"is_group": is_group,
	})
	if parent:
		doc.parent_warehouse = parent
	doc.insert(ignore_permissions=True)
	return doc.name


def _item_group(name, parent="All Item Groups"):
	if not frappe.db.exists("Item Group", name):
		frappe.get_doc({"doctype": "Item Group", "item_group_name": name,
		                "parent_item_group": parent, "is_group": 0}).insert(ignore_permissions=True)
	return name


def _uom(name):
	if not frappe.db.exists("UOM", name):
		frappe.get_doc({"doctype": "UOM", "uom_name": name}).insert(ignore_permissions=True)
	return name


def _item(code, name, group, uom, rate=0, is_stock=1, is_sales=0, is_purchase=1):
	if frappe.db.exists("Item", code):
		return code
	frappe.get_doc({
		"doctype": "Item", "item_code": code, "item_name": name,
		"item_group": group, "stock_uom": uom, "is_stock_item": is_stock,
		"is_sales_item": is_sales, "is_purchase_item": is_purchase,
		"valuation_rate": rate, "standard_rate": rate,
		"include_item_in_manufacturing": 1,
		"description": name,
	}).insert(ignore_permissions=True)
	return code


def _price_lists(company):
	"""Standard Selling / Standard Buying — normally seeded by the setup wizard.
	Sales Invoice and Purchase Receipt both make a price list mandatory."""
	currency = frappe.db.get_value("Company", company, "default_currency") or "INR"
	for name, selling, buying in (("Standard Selling", 1, 0), ("Standard Buying", 0, 1)):
		if frappe.db.exists("Price List", name):
			continue
		frappe.get_doc({
			"doctype": "Price List", "price_list_name": name, "currency": currency,
			"selling": selling, "buying": buying, "enabled": 1,
		}).insert(ignore_permissions=True)


def install():
	_erpnext_fixtures()
	company = _company()
	_price_lists(company)
	_fiscal_year()
	_uom("Cubic Meter")
	_uom("Litre")
	_uom("Kg")
	_uom("Ton")

	_item_group("RMC Raw Material")
	_item_group("Ready Mix Concrete")

	store = _warehouse("RMC Plant Store", company, is_group=1)
	finished = _warehouse("Finished Concrete", company)

	# ---- raw material items + one warehouse (silo) each ----
	for code, name, mtype, uom, rate in RAW_MATERIALS:
		_item(code, name, "RMC Raw Material", uom, rate=rate, is_sales=0)

	# ---- plant ----
	if not frappe.db.exists("RMC Plant", PLANT_NAME):
		frappe.get_doc({
			"doctype": "RMC Plant", "plant_name": PLANT_NAME, "company": company,
			"location": "Visakhapatnam, Andhra Pradesh", "capacity_m3_hr": 60,
			"commissioned_on": "2024-04-01",
			"store_warehouse": store, "finished_warehouse": finished, "is_active": 1,
		}).insert(ignore_permissions=True)

	# ---- silos, each with its own warehouse so stock IS the silo level ----
	for silo_name, mtype, item, cap in SILOS:
		wh = _warehouse(silo_name, company, parent=store)
		if frappe.db.exists("Silo", silo_name):
			frappe.db.set_value("Silo", silo_name, {
				"warehouse": wh, "item_code": item, "capacity_mt": cap,
				"material_type": mtype, "plant": PLANT_NAME,
			})
			continue
		frappe.get_doc({
			"doctype": "Silo", "silo_name": silo_name, "plant": PLANT_NAME,
			"material_type": mtype, "item_code": item, "warehouse": wh,
			"capacity_mt": cap, "min_level_mt": round(cap * 0.15, 2), "is_active": 1,
		}).insert(ignore_permissions=True)

	# ---- grades + their sellable concrete items ----
	for grade, mpa, app, rate in GRADES:
		item_code = "RMC-%s" % grade
		_item(item_code, "Ready Mix Concrete %s" % grade, "Ready Mix Concrete",
		      "Cubic Meter", rate=rate, is_sales=1, is_purchase=0)
		if frappe.db.exists("Concrete Grade", grade):
			frappe.db.set_value("Concrete Grade", grade, {
				"strength_mpa": mpa, "application": app,
				"item_code": item_code, "default_rate": rate, "is_active": 1})
			continue
		frappe.get_doc({
			"doctype": "Concrete Grade", "grade": grade, "strength_mpa": mpa,
			"application": app, "item_code": item_code, "default_rate": rate,
			"is_active": 1,
		}).insert(ignore_permissions=True)

	# ---- mix designs ----
	_build_mix_designs()

	# ---- settings ----
	s = frappe.get_single("RMC Settings")
	s.default_plant = PLANT_NAME
	s.company = company
	if s.auto_create_sales_invoice is None:
		s.auto_create_sales_invoice = 1
	s.auto_stock_entry = 1
	s.low_stock_alert = 1
	s.breakdown_alert = 1
	s.target_availability_pct = 90
	s.save(ignore_permissions=True)

	frappe.db.commit()
	print("  + company: %s" % company)
	print("  + items: %d raw + %d concrete grades" % (len(RAW_MATERIALS), len(GRADES)))
	print("  + silos: %d" % len(SILOS))
	print("  + mix designs: %d" % frappe.db.count("Mix Design"))


def _build_mix_designs():
	item_of = {
		"cement": "RM-CEM-OPC53", "flyash": "RM-FLYASH", "sand": "RM-SAND",
		"agg20": "RM-AGG20", "agg10": "RM-AGG10", "admix": "RM-ADMIX", "water": "RM-WATER",
	}
	type_of = {
		"RM-CEM-OPC53": "Cement", "RM-FLYASH": "Fly Ash", "RM-SAND": "Sand",
		"RM-AGG20": "Aggregate", "RM-AGG10": "Aggregate", "RM-ADMIX": "Admixture",
		"RM-WATER": "Water",
	}
	rates = {code: rate for code, _n, _t, _u, rate in RAW_MATERIALS}
	uoms = {code: uom for code, _n, _t, uom, _r in RAW_MATERIALS}

	for grade, (cem, fly, sand, a20, a10, adm, wat, wc) in MIX.items():
		if frappe.db.exists("Mix Design", {"grade": grade}):
			continue
		rows = []
		for key, qty in (("cement", cem), ("flyash", fly), ("sand", sand),
		                 ("agg20", a20), ("agg10", a10), ("admix", adm), ("water", wat)):
			if not qty:
				continue
			code = item_of[key]
			rows.append({
				"item_code": code, "material_type": type_of[code], "qty_per_m3": qty,
				"uom": uoms[code], "rate": rates[code], "amount": qty * rates[code],
			})
		doc = frappe.get_doc({
			"doctype": "Mix Design", "grade": grade, "plant": PLANT_NAME,
			"design_version": "1.0", "effective_from": "2025-04-01",
			"water_cement_ratio": wc, "slump_target_mm": 100 if grade < "M30" else 120,
			"is_active": 1, "approved_by": "Quality Head",
			"items": rows,
			"remarks": "IS 10262 based plant mix for %s." % grade,
		})
		doc.insert(ignore_permissions=True)


install_masters = install

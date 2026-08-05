"""End-to-end audit of the RMC app on a live site.

Every check asserts something a user would actually notice — that the schema is
there, that the document chain posts real stock and real revenue, that derived
numbers reconcile with the ledgers, that reports run and workspaces render.

    bench --site rmc.local execute rmc.setup.audit.run

Prints one line per check and a PASS/FAIL tally; returns the failures.
"""

import json
import frappe
from frappe.utils import flt, add_days, getdate, get_datetime

RESULTS = []


def _ok(label, detail=""):
	RESULTS.append(("PASS", label, detail))


def _fail(label, detail=""):
	RESULTS.append(("FAIL", label, detail))


def _check(cond, label, detail=""):
	_ok(label, detail) if cond else _fail(label, detail)


# ---------------------------------------------------------------- schema
def _schema():
	from rmc.setup.build_doctypes import doctypes

	for dt in doctypes():
		exists = frappe.db.exists("DocType", dt["name"])
		module = frappe.db.get_value("DocType", dt["name"], "module") if exists else None
		_check(exists and module == dt["module"],
		       "DocType %s in module %s" % (dt["name"], dt["module"]),
		       "found in %s" % module if exists else "missing")

	for role in ("RMC Manager", "Plant Operator", "Dispatch Incharge",
	             "Quality Engineer", "RMC Accounts"):
		_check(frappe.db.exists("Role", role), "Role %s" % role)

	for cf in ("Sales Invoice-rmc_delivery_challan", "Stock Entry-rmc_batch_production",
	           "Purchase Receipt-rmc_material_inward", "Customer-rmc_credit_status"):
		_check(frappe.db.exists("Custom Field", cf), "Custom field %s" % cf)


# ---------------------------------------------------------------- masters
def _masters():
	from rmc.setup.masters import GRADES, RAW_MATERIALS, SILOS, PLANT_NAME

	_check(frappe.db.exists("RMC Plant", PLANT_NAME), "Plant master exists")
	_check(frappe.db.count("Concrete Grade") >= len(GRADES),
	       "All %d concrete grades" % len(GRADES),
	       "%d found" % frappe.db.count("Concrete Grade"))
	_check(frappe.db.count("Mix Design") >= len(GRADES),
	       "A mix design per grade", "%d found" % frappe.db.count("Mix Design"))
	_check(frappe.db.count("Silo") >= len(SILOS), "All %d silos / yards" % len(SILOS))

	missing_items = [g for g, *_ in GRADES if not frappe.db.exists("Item", "RMC-%s" % g)]
	_check(not missing_items, "Every grade has a sellable item", str(missing_items))

	no_wh = [s.name for s in frappe.get_all("Silo", fields=["name", "warehouse"])
	         if not s.warehouse]
	_check(not no_wh, "Every silo is wired to a warehouse", str(no_wh))

	# each mix design must batch a sane weight of concrete
	bad = []
	for md in frappe.get_all("Mix Design", fields=["name", "total_weight_kg", "grade"]):
		if not (1800 <= flt(md.total_weight_kg) <= 2800):
			bad.append("%s=%s" % (md.grade, md.total_weight_kg))
	_check(not bad, "Mix designs batch 1800-2800 kg/m³", str(bad))


# ---------------------------------------------------------------- data volume
def _volume():
	counts = {
		"Concrete Order": frappe.db.count("Concrete Order", {"docstatus": 1}),
		"Batch Production": frappe.db.count("Batch Production", {"docstatus": 1}),
		"Delivery Challan": frappe.db.count("Delivery Challan", {"docstatus": 1}),
		"Material Inward": frappe.db.count("Material Inward", {"docstatus": 1}),
		"Cube Test": frappe.db.count("Cube Test", {"docstatus": 1}),
		"Plant Status Log": frappe.db.count("Plant Status Log"),
		"Power Log": frappe.db.count("Power Log"),
		"Breakdown Log": frappe.db.count("Breakdown Log"),
	}
	for dt, n in counts.items():
		_check(n > 0, "Demo data present: %s" % dt, "%d records" % n)

	days = frappe.db.sql("""SELECT COUNT(DISTINCT production_date)
	                        FROM `tabBatch Production` WHERE docstatus=1""")[0][0]
	_check(days >= 20, "Production spans a month of days", "%d distinct days" % days)


# ---------------------------------------------------------------- the chain
def _chain():
	"""Every submitted document must have produced its ERPNext counterpart."""
	no_se = frappe.get_all("Batch Production",
	                       filters={"docstatus": 1, "stock_entry": ["in", ["", None]]},
	                       pluck="name")
	_check(not no_se, "Every batch posted a Stock Entry", "%d without" % len(no_se))

	no_si = frappe.get_all("Delivery Challan",
	                       filters={"docstatus": 1, "sales_invoice": ["in", ["", None]]},
	                       pluck="name")
	_check(not no_si, "Every challan raised a Sales Invoice", "%d without" % len(no_si))

	no_pr = frappe.get_all("Material Inward",
	                       filters={"docstatus": 1, "purchase_receipt": ["in", ["", None]]},
	                       pluck="name")
	_check(not no_pr, "Every inward raised a Purchase Receipt", "%d without" % len(no_pr))

	# produced m³ must equal the concrete quantity in the stock ledger
	produced = flt(frappe.db.sql("""SELECT SUM(qty_m3) FROM `tabBatch Production`
	                                WHERE docstatus=1""")[0][0])
	in_ledger = flt(frappe.db.sql("""
		SELECT SUM(sed.qty) FROM `tabStock Entry Detail` sed
		JOIN `tabStock Entry` se ON se.name = sed.parent
		WHERE se.docstatus=1 AND se.rmc_batch_production IS NOT NULL
		  AND sed.item_code LIKE 'RMC-M%' AND sed.t_warehouse IS NOT NULL""")[0][0])
	_check(abs(produced - in_ledger) < 0.5,
	       "Produced m³ reconciles with the stock ledger",
	       "%.2f produced vs %.2f in ledger" % (produced, in_ledger))

	# dispatched m³ must equal what was invoiced
	dispatched = flt(frappe.db.sql("""SELECT SUM(qty_m3) FROM `tabDelivery Challan`
	                                  WHERE docstatus=1""")[0][0])
	invoiced = flt(frappe.db.sql("""
		SELECT SUM(sii.qty) FROM `tabSales Invoice Item` sii
		JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE si.docstatus=1 AND si.rmc_delivery_challan IS NOT NULL""")[0][0])
	_check(abs(dispatched - invoiced) < 0.5,
	       "Dispatched m³ reconciles with invoiced m³",
	       "%.2f dispatched vs %.2f invoiced" % (dispatched, invoiced))

	# challan value must equal invoice value
	chal_val = flt(frappe.db.sql("""SELECT SUM(amount) FROM `tabDelivery Challan`
	                                WHERE docstatus=1""")[0][0])
	inv_val = flt(frappe.db.sql("""
		SELECT SUM(si.net_total) FROM `tabSales Invoice` si
		WHERE si.docstatus=1 AND si.rmc_delivery_challan IS NOT NULL""")[0][0])
	_check(abs(chal_val - inv_val) < 5,
	       "Challan value reconciles with invoice value",
	       "%.2f vs %.2f" % (chal_val, inv_val))

	# order progress must equal the sum of its challans
	bad = []
	for o in frappe.get_all("Concrete Order", filters={"docstatus": 1},
	                        fields=["name", "order_qty_m3", "delivered_qty_m3",
	                                "pending_qty_m3", "status"]):
		delivered = flt(frappe.db.sql("""SELECT SUM(qty_m3) FROM `tabDelivery Challan`
		                                 WHERE docstatus=1 AND concrete_order=%s""",
		                              o.name)[0][0])
		if abs(delivered - flt(o.delivered_qty_m3)) > 0.01:
			bad.append("%s: field %.2f vs challans %.2f"
			           % (o.name, o.delivered_qty_m3, delivered))
		elif abs(flt(o.order_qty_m3) - flt(o.delivered_qty_m3)
		         - flt(o.pending_qty_m3)) > 0.01 and o.status != "Cancelled":
			bad.append("%s: ordered != delivered + pending" % o.name)
	_check(not bad, "Order delivered/pending reconcile with challans", "; ".join(bad[:3]))

	over = frappe.db.sql("""
		SELECT co.name FROM `tabConcrete Order` co
		WHERE co.docstatus=1 AND co.delivered_qty_m3 > co.order_qty_m3 + 0.01""")
	_check(not over, "No order is over-delivered", str(over[:3]))


# ---------------------------------------------------------------- derived values
def _derived():
	bad = frappe.db.sql("""
		SELECT name, qty_m3, total_material_cost, cost_per_m3 FROM `tabBatch Production`
		WHERE docstatus=1 AND qty_m3 > 0
		  AND ABS(cost_per_m3 - total_material_cost/qty_m3) > 1""")
	_check(not bad, "Batch cost per m³ is consistent", str(bad[:2]))

	bad = frappe.db.sql("""
		SELECT name FROM `tabDelivery Challan`
		WHERE docstatus=1 AND ABS(amount - qty_m3*rate) > 1""")
	_check(not bad, "Challan amount = qty × rate", str(bad[:2]))

	bad = frappe.db.sql("""
		SELECT name FROM `tabDelivery Challan`
		WHERE docstatus=1 AND return_time IS NOT NULL AND cycle_time_min <= 0""")
	_check(not bad, "Cycle time computed on every returned trip", str(bad[:2]))

	bad = frappe.db.sql("""
		SELECT name, avg_strength_mpa, required_strength_mpa, result FROM `tabCube Test`
		WHERE docstatus=1 AND (
		    (avg_strength_mpa >= required_strength_mpa AND result != 'Pass') OR
		    (avg_strength_mpa <  required_strength_mpa AND result != 'Fail'))""")
	_check(not bad, "Cube test pass/fail matches the strength", str(bad[:2]))

	bad = frappe.db.sql("""
		SELECT name FROM `tabPlant Status Log`
		WHERE duration_hours <= 0 OR duration_hours > 24""")
	_check(not bad, "Plant status durations are sane", str(bad[:2]))

	bad = frappe.db.sql("""
		SELECT name FROM `tabMaterial Inward`
		WHERE docstatus=1 AND ABS(net_weight - (gross_weight - tare_weight)) > 0.01""")
	_check(not bad, "Weighbridge net = gross − tare", str(bad[:2]))

	# consumption should track the recipe within the dosing tolerance
	worst = frappe.db.sql("""
		SELECT bm.parent, bm.item_code, bm.variance_pct FROM `tabBatch Material` bm
		JOIN `tabBatch Production` bp ON bp.name = bm.parent
		WHERE bp.docstatus=1 AND ABS(bm.variance_pct) > 5 LIMIT 3""")
	_check(not worst, "Material consumption within ±5% of recipe", str(worst))


# ---------------------------------------------------------------- stock
def _stock():
	negative = frappe.db.sql("""
		SELECT b.item_code, b.warehouse, b.actual_qty FROM `tabBin` b
		JOIN `tabSilo` s ON s.warehouse = b.warehouse AND s.item_code = b.item_code
		WHERE b.actual_qty < 0""")
	_check(not negative, "No silo has gone negative", str(negative[:3]))

	stocked = frappe.db.sql("""
		SELECT COUNT(*) FROM `tabBin` b
		JOIN `tabSilo` s ON s.warehouse = b.warehouse AND s.item_code = b.item_code
		WHERE b.actual_qty > 0""")[0][0]
	_check(stocked >= 8, "Silos hold stock", "%d silos with stock" % stocked)

	gl = flt(frappe.db.sql("""SELECT SUM(credit) FROM `tabGL Entry`
	                          WHERE is_cancelled=0 AND account LIKE 'Sales%'""")[0][0])
	_check(gl > 0, "Revenue posted to the general ledger", "%.2f credited to Sales" % gl)


# ---------------------------------------------------------------- reports
def _reports():
	from frappe.desk.query_report import run as run_report
	from rmc.setup.reports import REPORTS

	for r in REPORTS:
		name = r["name"]
		if not frappe.db.exists("Report", name):
			_fail("Report %s exists" % name)
			continue
		try:
			res = run_report(name, ignore_prepared_report=True)
			rows = res.get("result") or []
			_check(len(rows) > 0, "Report runs with data: %s" % name, "%d rows" % len(rows))
		except Exception as e:
			_fail("Report runs: %s" % name, str(e)[:120])


# ---------------------------------------------------------------- desk
def _desk():
	for ws in ("RMC Dashboard", "RMC Production", "RMC Materials", "RMC Dispatch",
	           "RMC Quality", "RMC Setup"):
		if not frappe.db.exists("Workspace", ws):
			_fail("Workspace %s" % ws)
			continue
		doc = frappe.get_doc("Workspace", ws)
		blocks = json.loads(doc.content or "[]")
		_check(len(blocks) >= 4 and len(doc.links) > 0,
		       "Workspace %s has content" % ws,
		       "%d blocks, %d links, %d shortcuts" % (len(blocks), len(doc.links),
		                                              len(doc.shortcuts)))

	# count only this app's cards/charts — the site also carries ERPNext's own
	from rmc.setup.workspaces import _cards, _charts

	mine = [c for _k, label, dt, *_r in _cards()
	        if (c := frappe.db.get_value("Number Card", {"label": label, "document_type": dt}))]
	chart_names = [c for _k, label, *_r in _charts()
	               if (c := frappe.db.get_value("Dashboard Chart", {"chart_name": label}))]
	_check(len(mine) >= 10, "RMC number cards created", "%d of %d" % (len(mine), len(_cards())))
	_check(len(chart_names) >= 8, "RMC dashboard charts created",
	       "%d of %d" % (len(chart_names), len(_charts())))

	_check(frappe.db.exists("Print Format", "RMC Delivery Challan"),
	       "Delivery Challan print format")

	# the print format must actually render for a real challan
	challan = frappe.db.get_value("Delivery Challan", {"docstatus": 1}, "name")
	if challan:
		try:
			from frappe.www.printview import get_html_and_style
			html = get_html_and_style(doc=frappe.get_doc("Delivery Challan", challan).as_json(),
			                          print_format="RMC Delivery Challan")["html"]
			_check("DELIVERY CHALLAN" in html and challan in html,
			       "Challan print format renders", "%d chars" % len(html))
		except Exception as e:
			_fail("Challan print format renders", str(e)[:140])


# ---------------------------------------------------------------- live rules
def _rules():
	"""The guard rails must actually fire — checked by trying to break them."""
	order = frappe.db.get_value("Concrete Order", {"docstatus": 1, "status": "Completed"},
	                            "name") or frappe.db.get_value(
		"Concrete Order", {"docstatus": 1}, "name")
	if not order:
		_fail("Over-delivery is blocked", "no order to test against")
		return

	o = frappe.get_doc("Concrete Order", order)
	mixer = frappe.db.get_value("Transit Mixer", {"vehicle_type": "Transit Mixer"}, "name")
	dc = frappe.get_doc({
		"doctype": "Delivery Challan", "concrete_order": o.name, "challan_date": getdate(),
		"grade": o.grade, "qty_m3": flt(o.order_qty_m3) + 50, "rate": o.rate,
		"transit_mixer": mixer, "dispatch_time": get_datetime(),
	})
	try:
		dc.insert(ignore_permissions=True)
		_fail("Over-delivery is blocked", "a challan 50 m³ over the order was accepted")
		frappe.delete_doc("Delivery Challan", dc.name, force=True, ignore_permissions=True)
	except frappe.ValidationError:
		_ok("Over-delivery is blocked")
	frappe.db.rollback()

	# a mix design for the wrong grade must be rejected
	bp = frappe.db.get_value("Batch Production", {"docstatus": 1}, "name")
	if bp:
		src = frappe.get_doc("Batch Production", bp)
		other_grade = frappe.db.get_value("Concrete Grade",
		                                  {"grade": ["!=", src.grade]}, "grade")
		wrong = frappe.copy_doc(src)
		wrong.grade = other_grade
		try:
			wrong.insert(ignore_permissions=True)
			_fail("Mix design must match the grade", "mismatched design accepted")
		except frappe.ValidationError:
			_ok("Mix design must match the grade")
		frappe.db.rollback()

	# customer on credit hold cannot order
	cust = frappe.db.get_value("Customer", {}, "name")
	site = frappe.db.get_value("Construction Site", {"customer": cust}, "name")
	if cust and site:
		frappe.db.set_value("Customer", cust, "rmc_credit_status", "Hold")
		try:
			frappe.get_doc({
				"doctype": "Concrete Order", "customer": cust, "construction_site": site,
				"order_date": getdate(), "grade": "M25", "order_qty_m3": 10, "rate": 5000,
				"required_from": getdate(),
			}).insert(ignore_permissions=True)
			_fail("Credit hold blocks new orders", "order accepted for a held customer")
		except frappe.ValidationError:
			_ok("Credit hold blocks new orders")
		frappe.db.rollback()
		frappe.db.set_value("Customer", cust, "rmc_credit_status", "Normal")
		frappe.db.commit()


# ---------------------------------------------------------------- runner
def run():
	global RESULTS
	RESULTS = []
	for fn in (_schema, _masters, _volume, _chain, _derived, _stock, _reports, _desk, _rules):
		try:
			fn()
		except Exception:
			_fail("audit section %s crashed" % fn.__name__, frappe.get_traceback()[-400:])

	passed = [r for r in RESULTS if r[0] == "PASS"]
	failed = [r for r in RESULTS if r[0] == "FAIL"]
	for status, label, detail in RESULTS:
		print("%s  %s%s" % (status, label, ("  [%s]" % detail) if detail else ""))
	print("\n%d checks: %d PASS, %d FAIL" % (len(RESULTS), len(passed), len(failed)))
	return {"pass": len(passed), "fail": len(failed),
	        "failures": [(l, d) for s, l, d in failed]}

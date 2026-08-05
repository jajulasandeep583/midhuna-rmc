"""Six role-scoped Workspaces for RMC Plant Management (code-driven, idempotent).

Each workspace carries an icon + indicator colour, an intro paragraph, number
cards, group-by charts, shortcuts and grouped sidebar links.

_make_workspace UPSERTS, so edits here always land on the next migrate.
"""

import json
import frappe

SM = "System Manager"

COLORS = {
	"RMC Dashboard": "blue",
	"RMC Management": "purple",
	"RMC Production": "green",
	"RMC Materials": "orange",
	"RMC Dispatch": "purple",
	"RMC Quality": "red",
	"RMC Setup": "gray",
}

INTRO = {
	"RMC Management": "Sales, production, purchase, stock and receivables in one place — the owner's view of the plant. Pick any period; every number drills down.",
	"RMC Dashboard": "The plant at a glance — today's production, dispatches, orders in hand and "
	             "live plant status. Start here every morning; drill into any number from the "
	             "cards and charts below.",
	"RMC Production": "Batch the concrete: pick the mix design for the grade, record what was "
	              "actually consumed against the recipe, and the stock entry writes itself. "
	              "Used all shift by the batching operator.",
	"RMC Materials": "Weighbridge inwards of cement, sand, aggregate, fly ash and "
	                           "admixture into their silos and yards, and the running stock "
	                           "level of every silo. Used by the stores and weighbridge desk.",
	"RMC Dispatch": "Customer orders, truck allocation and the delivery challan that "
	                         "travels with every load — dispatch time, site arrival, slump and "
	                         "the signed return. Used by the dispatch incharge.",
	"RMC Quality": "Cube tests against the design strength, plus plant running / idle "
	                         "/ breakdown time, power consumption and maintenance due. Used by "
	                         "the quality engineer and plant maintenance.",
	"RMC Setup": "Master data — plant, grades, mix designs, transit mixers, customer sites and "
	             "silos. Set this up once before daily operations begin.",
}


# ------------------------- number cards -------------------------
def _cards():
	return [
		("today_production", "Today's Production (m³)", "Batch Production", "Sum", "qty_m3",
		 [["Batch Production", "production_date", "Timespan", "today"],
		  ["Batch Production", "docstatus", "=", 1]]),
		("today_dispatch", "Today's Dispatch (m³)", "Delivery Challan", "Sum", "qty_m3",
		 [["Delivery Challan", "challan_date", "Timespan", "today"],
		  ["Delivery Challan", "docstatus", "=", 1]]),
		("today_trips", "Today's Trips", "Delivery Challan", "Count", None,
		 [["Delivery Challan", "challan_date", "Timespan", "today"],
		  ["Delivery Challan", "docstatus", "=", 1]]),
		("open_orders", "Open Orders", "Concrete Order", "Count", None,
		 [["Concrete Order", "status", "in", ["Open", "In Progress"]],
		  ["Concrete Order", "docstatus", "=", 1]]),
		("pending_qty", "Pending Order Qty (m³)", "Concrete Order", "Sum", "pending_qty_m3",
		 [["Concrete Order", "status", "in", ["Open", "In Progress"]],
		  ["Concrete Order", "docstatus", "=", 1]]),
		("month_revenue", "This Month Dispatch Value", "Delivery Challan", "Sum", "amount",
		 [["Delivery Challan", "challan_date", "Timespan", "this month"],
		  ["Delivery Challan", "docstatus", "=", 1]]),
		("open_breakdowns", "Open Breakdowns", "Breakdown Log", "Count", None,
		 [["Breakdown Log", "status", "in", ["Open", "In Progress"]]]),
		("cube_fails", "Failed Cube Tests", "Cube Test", "Count", None,
		 [["Cube Test", "result", "=", "Fail"], ["Cube Test", "docstatus", "=", 1]]),
		("inward_month", "Material Inward (MT) - Month", "Material Inward", "Sum", "net_weight",
		 [["Material Inward", "inward_date", "Timespan", "this month"],
		  ["Material Inward", "docstatus", "=", 1]]),
		("mixers_available", "Mixers Available", "Transit Mixer", "Count", None,
		 [["Transit Mixer", "status", "=", "Available"]]),
		("maint_due", "Maintenance Due", "RMC Maintenance Task", "Count", None,
		 [["RMC Maintenance Task", "status", "in", ["Due", "Overdue"]]]),
		("active_sites", "Active Customer Sites", "Construction Site", "Count", None,
		 [["Construction Site", "is_active", "=", 1]]),
	]


def _ensure_cards():
	names = {}
	for key, label, dt, func, agg, filters in _cards():
		if not frappe.db.exists("DocType", dt):
			continue
		existing = frappe.db.get_value("Number Card", {"label": label, "document_type": dt}, "name")
		if existing:
			names[key] = existing
			continue
		payload = {"doctype": "Number Card", "label": label, "type": "Document Type",
		           "document_type": dt, "function": func, "is_public": 1,
		           "show_percentage_stats": 0, "filters_json": json.dumps(filters)}
		if agg:
			payload["aggregate_function_based_on"] = agg
		try:
			names[key] = frappe.get_doc(payload).insert(ignore_permissions=True).name
		except Exception:
			frappe.log_error(frappe.get_traceback(), "RMC: number card %s failed" % label)
	return names


# ------------------------- charts -------------------------
def _charts():
	"""(key, label, doctype, group_by_field, chart type, filters, aggregate field)"""
	return [
		("prod_by_grade", "Production by Grade (m³)", "Batch Production", "grade", "Bar",
		 [["Batch Production", "docstatus", "=", 1]], "qty_m3"),
		("prod_by_shift", "Production by Shift (m³)", "Batch Production", "shift", "Pie",
		 [["Batch Production", "docstatus", "=", 1]], "qty_m3"),
		("dispatch_customer", "Dispatch by Customer (m³)", "Delivery Challan", "customer", "Bar",
		 [["Delivery Challan", "docstatus", "=", 1]], "qty_m3"),
		("order_status", "Orders by Status", "Concrete Order", "status", "Donut",
		 [["Concrete Order", "docstatus", "=", 1]], None),
		("inward_material", "Material Inward by Type (MT)", "Material Inward", "material_type", "Bar",
		 [["Material Inward", "docstatus", "=", 1]], "net_weight"),
		("plant_status", "Plant Time by Status (hrs)", "Plant Status Log", "status", "Pie",
		 [], "duration_hours"),
		("breakdown_equip", "Breakdowns by Equipment", "Breakdown Log", "equipment", "Bar", [], None),
		("cube_result", "Cube Test Results", "Cube Test", "result", "Donut",
		 [["Cube Test", "docstatus", "=", 1]], None),
		("mixer_trips", "Trips by Transit Mixer", "Delivery Challan", "transit_mixer", "Bar",
		 [["Delivery Challan", "docstatus", "=", 1]], None),
	]


def _ensure_charts():
	names = {}
	for key, label, dt, based_on, ctype, filters, agg in _charts():
		if not frappe.db.exists("DocType", dt):
			continue
		try:
			fj = json.dumps(filters)
			existing = frappe.db.get_value("Dashboard Chart", {"chart_name": label}, "name")
			payload = {
				"doctype": "Dashboard Chart", "chart_name": label, "chart_type": "Group By",
				"document_type": dt, "group_by_based_on": based_on,
				"type": ctype, "is_public": 1, "timeseries": 0, "filters_json": fj,
				"group_by_type": "Sum" if agg else "Count",
			}
			if agg:
				payload["aggregate_function_based_on"] = agg
			if existing:
				doc = frappe.get_doc("Dashboard Chart", existing)
				doc.update({k: v for k, v in payload.items() if k not in ("doctype",)})
				doc.save(ignore_permissions=True)
				names[key] = existing
				continue
			names[key] = frappe.get_doc(payload).insert(ignore_permissions=True).name
		except Exception:
			frappe.log_error(frappe.get_traceback(), "RMC: chart %s failed" % label)
	return names


# ------------------------- workspace specs -------------------------
def _workspaces():
	return [
		{
			"name": "RMC Management", "icon": "rmc-dashboard",
			"roles": ["RMC Manager", "RMC Accounts"],
			"shortcuts": [
				("Page", "Management", "rmc-manage"),
				("Page", "Report Hub", "rmc-reports"),
				("Page", "How to Use RMC", "rmc-guide"),
				("Report", "RMC Profit and Loss", "RMC Profit and Loss"),
				("URL", "Public Dashboard", "/rmc"),
				("URL", "Public P&L", "/rmc/pl"),
				("Report", "Grade Profitability", "Grade Profitability"),
				("Report", "Monthly Plant Summary", "Monthly Plant Summary"),
				("Report", "Customer Wise Sales", "Customer Wise Sales"),
				("DocType", "Sales Invoice", "Sales Invoice"),
			],
			"cards": ["month_revenue", "open_orders", "pending_qty", "today_dispatch"],
			"charts": ["dispatch_customer", "order_status"],
			"links": [
				("Management", [
					("Page", "rmc-manage", "Management view"),
					("Page", "rmc-reports", "Report Hub"),
					("Page", "rmc-guide", "How to Use RMC")]),
				("Money", [
					("DocType", "Sales Invoice"), ("DocType", "Purchase Receipt"),
					("DocType", "Customer"), ("DocType", "Supplier")]),
				("Management Reports", [
					("Report", "RMC Profit and Loss"),
					("Report", "Monthly Plant Summary"),
					("Report", "Grade Profitability"),
					("Report", "Customer Wise Sales"),
					("Report", "Customer Order Status"),
					("Report", "Supplier Purchase Summary"),
					("Report", "Order Book and Pour Schedule")]),
			],
		},
		{
			"name": "RMC Dashboard", "icon": "getting-started",
			"roles": ["RMC Manager", "Plant Operator", "Dispatch Incharge"],
			"shortcuts": [
				("Page", "Management", "rmc-manage"),
				("Page", "RMC Control Tower", "rmc-control-tower"),
				("Page", "Live Plant Dashboard", "rmc-live-dashboard"),
				("Page", "Batching Board", "rmc-batch-board"),
				("Page", "Dispatch Board", "rmc-dispatch-board"),
				("Page", "Silo & Stock Board", "rmc-silo-board"),
				("Page", "Quality Board", "rmc-quality-board"),
				("DocType", "Batch Production", "Batch Production"),
				("DocType", "Delivery Challan", "Delivery Challan"),
				("DocType", "Concrete Order", "Concrete Order"),
				("DocType", "Material Inward", "Material Inward"),
				("Report", "Daily Production Summary", "Daily Production Summary"),
				("Report", "Plant Availability and Downtime", "Plant Availability and Downtime"),
			],
			"cards": ["today_production", "today_dispatch", "today_trips", "open_orders",
			          "pending_qty", "month_revenue", "open_breakdowns", "mixers_available"],
			"charts": ["prod_by_grade", "dispatch_customer", "order_status", "plant_status"],
			"links": [
				("Boards", [
					("Page", "rmc-control-tower", "RMC Control Tower"),
					("Page", "rmc-live-dashboard", "Live Plant Dashboard"),
					("Page", "rmc-batch-board", "Batching Board"),
					("Page", "rmc-dispatch-board", "Dispatch Board"),
					("Page", "rmc-silo-board", "Silo & Stock Board"),
					("Page", "rmc-quality-board", "Quality Board"),
					("Page", "rmc-order-360", "Order 360"),
					("Page", "rmc-reports", "Report Hub"),
					("Page", "rmc-guide", "How to Use RMC")]),
				("Daily Operations", [
					("DocType", "Batch Production"), ("DocType", "Delivery Challan"),
					("DocType", "Concrete Order"), ("DocType", "Material Inward")]),
				("MIS Reports", [
					("Report", "Daily Production Summary"),
					("Report", "Dispatch Register"),
					("Report", "Customer Order Status"),
					("Report", "Plant Availability and Downtime"),
					("Report", "Silo and Stock Status")]),
				("Setup", [
					("DocType", "RMC Plant"), ("DocType", "RMC Settings")]),
			],
		},
		{
			"name": "RMC Production", "icon": "milestone",
			"roles": ["Plant Operator", "RMC Manager"],
			"shortcuts": [
				("Page", "Batching Board", "rmc-batch-board"),
				("DocType", "Batch Production", "Batch Production"),
				("DocType", "Mix Design", "Mix Design"),
				("DocType", "Concrete Grade", "Concrete Grade"),
				("Report", "Batch Register", "Batch Register"),
				("Report", "Material Consumption vs Recipe", "Material Consumption vs Recipe"),
			],
			"cards": ["today_production", "pending_qty"],
			"charts": ["prod_by_grade", "prod_by_shift"],
			"links": [
				("RMC Production", [
					("DocType", "Batch Production"), ("DocType", "Cube Test")]),
				("Recipes", [
					("DocType", "Mix Design"), ("DocType", "Concrete Grade")]),
				("Reports", [
					("Report", "Daily Production Summary"),
					("Report", "Batch Register"),
					("Report", "Material Consumption vs Recipe"),
					("Report", "Production Target vs Actual"),
					("Report", "Grade Profitability"),
					("Report", "Slump Compliance")]),
			],
		},
		{
			"name": "RMC Materials", "icon": "stock",
			"roles": ["Plant Operator", "RMC Manager", "RMC Accounts"],
			"shortcuts": [
				("Page", "Silo & Stock Board", "rmc-silo-board"),
				("DocType", "Material Inward", "Material Inward"),
				("DocType", "Silo", "Silo"),
				("Report", "Material Inward Register", "Material Inward Register"),
				("Report", "Silo and Stock Status", "Silo and Stock Status"),
				("DocType", "Stock Entry", "Stock Entry"),
			],
			"cards": ["inward_month"],
			"charts": ["inward_material"],
			"links": [
				("Inward & Stock", [
					("DocType", "Material Inward"), ("DocType", "Silo"),
					("DocType", "Stock Entry"), ("DocType", "Purchase Receipt"),
					("DocType", "Stock Reconciliation")]),
				("Reports", [
					("Report", "Material Inward Register"),
					("Report", "Silo and Stock Status"),
					("Report", "Material Consumption vs Recipe"),
					("Report", "Supplier Purchase Summary")]),
			],
		},
		{
			"name": "RMC Dispatch", "icon": "delivery",
			"roles": ["Dispatch Incharge", "RMC Manager"],
			"shortcuts": [
				("Page", "Dispatch Board", "rmc-dispatch-board"),
				("Page", "Order 360", "rmc-order-360"),
				("DocType", "Delivery Challan", "Delivery Challan"),
				("DocType", "Concrete Order", "Concrete Order"),
				("DocType", "Transit Mixer", "Transit Mixer"),
				("DocType", "Construction Site", "Construction Site"),
				("Report", "Dispatch Register", "Dispatch Register"),
				("Report", "Vehicle Utilisation and Trips", "Vehicle Utilisation and Trips"),
			],
			"cards": ["today_dispatch", "today_trips", "open_orders", "mixers_available"],
			"charts": ["dispatch_customer", "mixer_trips", "order_status"],
			"links": [
				("Dispatch", [
					("DocType", "Delivery Challan"), ("DocType", "Concrete Order"),
					("DocType", "Transit Mixer"), ("DocType", "Driver")]),
				("Customers", [
					("DocType", "Customer"), ("DocType", "Construction Site"),
					("DocType", "Sales Invoice")]),
				("Reports", [
					("Report", "Dispatch Register"),
					("Report", "Customer Order Status"),
					("Report", "Vehicle Utilisation and Trips"),
					("Report", "Customer Wise Sales"),
					("Report", "Order Book and Pour Schedule"),
					("Report", "Driver Performance")]),
			],
		},
		{
			"name": "RMC Quality", "icon": "test",
			"roles": ["Quality Engineer", "Plant Operator", "RMC Manager"],
			"shortcuts": [
				("Page", "Quality Board", "rmc-quality-board"),
				("Page", "Live PLC Board", "rmc-plc-board"),
				("DocType", "Cube Test", "Cube Test"),
				("DocType", "Plant Status Log", "Plant Status Log"),
				("DocType", "Breakdown Log", "Breakdown Log"),
				("DocType", "RMC Maintenance Task", "Maintenance Schedule"),
				("DocType", "Power Log", "Power Log"),
				("Report", "Cube Test Register", "Cube Test Register"),
			],
			"cards": ["cube_fails", "open_breakdowns", "maint_due"],
			"charts": ["cube_result", "plant_status", "breakdown_equip"],
			"links": [
				("Quality", [("DocType", "Cube Test")]),
				("Live Signals", [
					("Page", "rmc-plc-board", "Live PLC Board"),
					("DocType", "RMC PLC Tag", "PLC Tags"),
					("DocType", "RMC PLC Reading", "PLC Readings")]),
				("Plant Operations", [
					("DocType", "Plant Status Log"), ("DocType", "Breakdown Log"),
					("DocType", "RMC Maintenance Task"), ("DocType", "Power Log")]),
				("Reports", [
					("Report", "Cube Test Register"),
					("Report", "Plant Availability and Downtime"),
					("Report", "Power and Diesel Consumption"),
					("Report", "Monthly Plant Summary")]),
			],
		},
		{
			"name": "RMC Setup", "icon": "setting",
			"roles": ["RMC Manager"],
			"shortcuts": [
				("DocType", "RMC Plant", "RMC Plant"),
				("DocType", "Concrete Grade", "Concrete Grade"),
				("DocType", "Mix Design", "Mix Design"),
				("DocType", "Silo", "Silo"),
				("DocType", "Transit Mixer", "Transit Mixer"),
				("DocType", "Construction Site", "Construction Site"),
			],
			"cards": ["active_sites", "mixers_available"],
			"charts": [],
			"links": [
				("Plant Masters", [
					("DocType", "RMC Plant"), ("DocType", "Silo"),
					("DocType", "RMC Settings")]),
				("Product Masters", [
					("DocType", "Concrete Grade"), ("DocType", "Mix Design"),
					("DocType", "Item")]),
				("Fleet & Customers", [
					("DocType", "Transit Mixer"), ("DocType", "Driver"),
					("DocType", "Construction Site"), ("DocType", "Customer"),
					("DocType", "Supplier")]),
			],
		},
	]


def _content(spec, card_ids, chart_ids, ws_shortcuts):
	name = spec["name"]
	blocks = [
		{"id": "hdr", "type": "header",
		 "data": {"text": "<span class=\"h4\"><b>%s</b></span>" % name, "col": 12}},
		{"id": "intro", "type": "paragraph", "data": {"text": "<p>%s</p>" % INTRO[name], "col": 12}},
	]
	for k in spec["cards"]:
		if card_ids.get(k):
			blocks.append({"id": "nc_" + k, "type": "number_card",
			               "data": {"number_card_name": card_ids[k], "col": 3}})
	for k in spec["charts"]:
		if chart_ids.get(k):
			blocks.append({"id": "ch_" + k, "type": "chart",
			               "data": {"chart_name": chart_ids[k], "col": 6}})
	for s in ws_shortcuts:
		blocks.append({"id": "sc_" + s["label"][:12].replace(" ", ""), "type": "shortcut",
		               "data": {"shortcut_name": s["label"], "col": 3}})
	for (grp, _items) in spec["links"]:
		blocks.append({"id": "cd_" + grp[:12].replace(" ", ""), "type": "card",
		               "data": {"card_name": grp, "col": 4}})
	return json.dumps(blocks)


def _make_workspace(spec, card_ids, chart_ids, seq):
	name = spec["name"]

	ws_shortcuts = []
	for sc in spec["shortcuts"]:
		stype, label, link_to = sc[0], sc[1], sc[2]
		if stype == "URL":
			# a public web page — the desk links straight out to it
			ws_shortcuts.append({"type": "URL", "label": label, "url": link_to,
			                     "color": "Green"})
		elif stype == "Page":
			if frappe.db.exists("Page", link_to):
				ws_shortcuts.append({"type": "Page", "label": label, "link_to": link_to,
				                     "color": "Green"})
		elif stype == "Report":
			if frappe.db.exists("Report", link_to):
				ws_shortcuts.append({
					"type": "Report", "label": label, "link_to": link_to,
					"report_ref_doctype": frappe.db.get_value("Report", link_to, "ref_doctype"),
					"color": "Grey"})
		elif frappe.db.exists("DocType", link_to):
			ws_shortcuts.append({"type": "DocType", "label": label, "link_to": link_to,
			                     "color": "Blue"})

	links = []
	for (grp, items) in spec["links"]:
		links.append({"type": "Card Break", "label": grp})
		for it in items:
			ltype, lname = it[0], it[1]
			if ltype == "URL":
				# Workspace Link only accepts DocType / Page / Report; a public
				# page belongs in shortcuts, which do take a URL.
				continue
			llabel = it[2] if len(it) > 2 else lname
			if ltype == "DocType" and frappe.db.exists("DocType", lname):
				links.append({"type": "Link", "link_type": "DocType", "link_to": lname,
				              "label": llabel, "onboard": 0, "is_query_report": 0})
			elif ltype == "Page" and frappe.db.exists("Page", lname):
				links.append({"type": "Link", "link_type": "Page", "link_to": lname,
				              "label": llabel, "onboard": 0})
			elif ltype == "Report" and frappe.db.exists("Report", lname):
				links.append({"type": "Link", "link_type": "Report", "link_to": lname,
				              "label": llabel, "is_query_report": 1, "onboard": 0,
				              "dependencies": frappe.db.get_value("Report", lname, "ref_doctype")})

	number_cards = [{"number_card_name": card_ids[k]} for k in spec["cards"] if card_ids.get(k)]
	charts = [{"chart_name": chart_ids[k], "label": chart_ids[k]}
	          for k in spec["charts"] if chart_ids.get(k)]
	roles = [{"role": r} for r in (spec["roles"] + [SM]) if frappe.db.exists("Role", r)]
	content = _content(spec, card_ids, chart_ids, ws_shortcuts)

	fields = {"title": name, "label": name, "module": "RMC Setup", "public": 1,
	          "icon": spec["icon"], "indicator_color": COLORS.get(name, "gray"),
	          "sequence_id": seq, "content": content, "parent_page": ""}

	if frappe.db.exists("Workspace", name):
		doc = frappe.get_doc("Workspace", name)
		doc.update(fields)
		doc.set("shortcuts", ws_shortcuts)
		doc.set("links", links)
		doc.set("number_cards", number_cards)
		doc.set("charts", charts)
		doc.set("roles", roles)
		doc.save(ignore_permissions=True)
	else:
		frappe.get_doc({"doctype": "Workspace", "name": name, **fields,
		                "shortcuts": ws_shortcuts, "links": links,
		                "number_cards": number_cards, "charts": charts,
		                "roles": roles}).insert(ignore_permissions=True)


def install():
	try:
		card_ids = _ensure_cards()
		chart_ids = _ensure_charts()
		for i, spec in enumerate(_workspaces(), start=1):
			_make_workspace(spec, card_ids, chart_ids, round(0.1 * i, 2))
		frappe.db.commit()
		print("  + workspaces: %d, cards: %d, charts: %d"
		      % (len(_workspaces()), len(card_ids), len(chart_ids)))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "RMC: workspaces setup failed")
		raise


create = install

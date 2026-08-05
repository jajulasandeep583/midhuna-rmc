"""Standard Query Reports for RMC Plant Management (code-driven, idempotent).

Created with is_standard = Yes so, in developer mode, each report is written to
its module folder as version-controlled files and ships with the app.

    bench --site rmc.local execute rmc.setup.reports.install
"""

import frappe

REPORTS = [
	{
		"name": "Daily Production Summary", "ref_doctype": "Batch Production",
		"module": "RMC Production",
		"query": """
SELECT
  bp.production_date                       AS "Date:Date:100",
  bp.shift                                 AS "Shift:Data:90",
  bp.grade                                 AS "Grade:Link/Concrete Grade:80",
  COUNT(bp.name)                           AS "Loads:Int:70",
  SUM(bp.no_of_batches)                    AS "Batches:Int:80",
  SUM(bp.qty_m3)                           AS "Produced m3:Float:110",
  SUM(bp.total_material_cost)              AS "Material Cost:Currency:130",
  SUM(bp.total_material_cost)/NULLIF(SUM(bp.qty_m3),0) AS "Cost / m3:Currency:110"
FROM `tabBatch Production` bp
WHERE bp.docstatus = 1
GROUP BY bp.production_date, bp.shift, bp.grade
ORDER BY bp.production_date DESC, bp.shift, bp.grade
""",
	},
	{
		"name": "Batch Register", "ref_doctype": "Batch Production",
		"module": "RMC Production",
		"query": """
SELECT
  bp.name                AS "Batch:Link/Batch Production:130",
  bp.production_date     AS "Date:Date:95",
  bp.shift               AS "Shift:Data:80",
  bp.grade               AS "Grade:Link/Concrete Grade:70",
  bp.mix_design          AS "Mix Design:Link/Mix Design:130",
  bp.qty_m3              AS "Qty m3:Float:80",
  bp.no_of_batches       AS "Batches:Int:75",
  bp.concrete_order      AS "Order:Link/Concrete Order:120",
  co.customer            AS "Customer:Link/Customer:150",
  bp.operator            AS "Operator:Data:110",
  bp.cost_per_m3         AS "Cost/m3:Currency:100",
  bp.stock_entry         AS "Stock Entry:Link/Stock Entry:140",
  bp.status              AS "Status:Data:90"
FROM `tabBatch Production` bp
LEFT JOIN `tabConcrete Order` co ON co.name = bp.concrete_order
WHERE bp.docstatus = 1
ORDER BY bp.production_date DESC, bp.name DESC
""",
	},
	{
		"name": "Material Consumption vs Recipe", "ref_doctype": "Batch Production",
		"module": "RMC Production",
		"query": """
SELECT
  bp.production_date        AS "Date:Date:100",
  bp.grade                  AS "Grade:Link/Concrete Grade:80",
  bm.item_code              AS "Item:Link/Item:180",
  bm.material_type          AS "Type:Data:100",
  SUM(bm.target_qty)        AS "Target Qty:Float:120",
  SUM(bm.actual_qty)        AS "Actual Qty:Float:120",
  SUM(bm.actual_qty) - SUM(bm.target_qty) AS "Variance:Float:110",
  100 * (SUM(bm.actual_qty) - SUM(bm.target_qty)) / NULLIF(SUM(bm.target_qty),0)
                            AS "Variance %:Float:110",
  SUM(bm.amount)            AS "Cost:Currency:120"
FROM `tabBatch Material` bm
JOIN `tabBatch Production` bp ON bp.name = bm.parent
WHERE bp.docstatus = 1
GROUP BY bp.production_date, bp.grade, bm.item_code, bm.material_type
ORDER BY bp.production_date DESC, bp.grade, bm.item_code
""",
	},
	{
		"name": "Production Target vs Actual", "ref_doctype": "Concrete Order",
		"module": "RMC Production",
		"query": """
SELECT
  co.name                AS "Order:Link/Concrete Order:120",
  co.customer            AS "Customer:Link/Customer:160",
  cs.site_name           AS "Site:Data:150",
  co.grade               AS "Grade:Link/Concrete Grade:70",
  co.order_qty_m3        AS "Ordered m3:Float:100",
  co.delivered_qty_m3    AS "Delivered m3:Float:110",
  co.pending_qty_m3      AS "Pending m3:Float:100",
  100 * co.delivered_qty_m3 / NULLIF(co.order_qty_m3,0) AS "Achieved %:Float:100",
  co.required_from       AS "Required From:Date:110",
  co.status              AS "Status:Data:100"
FROM `tabConcrete Order` co
LEFT JOIN `tabConstruction Site` cs ON cs.name = co.construction_site
WHERE co.docstatus = 1
ORDER BY co.required_from DESC
""",
	},
	{
		"name": "Material Inward Register", "ref_doctype": "Material Inward",
		"module": "RMC Materials",
		"query": """
SELECT
  mi.name             AS "Inward:Link/Material Inward:130",
  mi.inward_date      AS "Date:Date:95",
  mi.supplier         AS "Supplier:Link/Supplier:170",
  mi.item_code        AS "Item:Link/Item:180",
  mi.material_type    AS "Type:Data:95",
  mi.vehicle_no       AS "Vehicle:Data:110",
  mi.gross_weight     AS "Gross MT:Float:95",
  mi.tare_weight      AS "Tare MT:Float:95",
  mi.net_weight       AS "Net MT:Float:95",
  mi.rate             AS "Rate:Currency:90",
  mi.amount           AS "Amount:Currency:120",
  mi.silo             AS "Silo:Link/Silo:140",
  mi.purchase_receipt AS "Purchase Receipt:Link/Purchase Receipt:150"
FROM `tabMaterial Inward` mi
WHERE mi.docstatus = 1
ORDER BY mi.inward_date DESC, mi.name DESC
""",
	},
	{
		"name": "Silo and Stock Status", "ref_doctype": "Silo",
		"module": "RMC Materials",
		"query": """
SELECT
  s.silo_name        AS "Silo / Yard:Link/Silo:170",
  s.material_type    AS "Material:Data:110",
  s.item_code        AS "Item:Link/Item:180",
  s.capacity_mt      AS "Capacity:Float:100",
  IFNULL(b.actual_qty,0)/1000 AS "Stock (MT/kL):Float:130",
  100 * IFNULL(b.actual_qty,0)/1000 / NULLIF(s.capacity_mt,0) AS "Filled %:Float:95",
  s.min_level_mt     AS "Low Level:Float:100",
  CASE WHEN IFNULL(b.actual_qty,0)/1000 <= s.min_level_mt THEN 'LOW - REORDER'
       ELSE 'OK' END AS "Alert:Data:130",
  IFNULL(b.stock_value,0) AS "Stock Value:Currency:130",
  s.warehouse        AS "Warehouse:Link/Warehouse:180"
FROM `tabSilo` s
LEFT JOIN `tabBin` b ON b.warehouse = s.warehouse AND b.item_code = s.item_code
WHERE s.is_active = 1
ORDER BY s.material_type, s.silo_name
""",
	},
	{
		"name": "Dispatch Register", "ref_doctype": "Delivery Challan",
		"module": "RMC Dispatch",
		"query": """
SELECT
  dc.name              AS "Challan:Link/Delivery Challan:130",
  dc.challan_date      AS "Date:Date:95",
  dc.customer          AS "Customer:Link/Customer:160",
  cs.site_name         AS "Site:Data:150",
  dc.grade             AS "Grade:Link/Concrete Grade:70",
  dc.qty_m3            AS "Qty m3:Float:80",
  dc.rate              AS "Rate:Currency:95",
  dc.amount            AS "Amount:Currency:120",
  dc.transit_mixer     AS "Vehicle:Link/Transit Mixer:110",
  dc.driver_name       AS "Driver:Data:130",
  dc.dispatch_time     AS "Dispatch:Datetime:140",
  dc.cycle_time_min    AS "Cycle (min):Int:100",
  dc.slump_mm          AS "Slump:Int:70",
  dc.status            AS "Status:Data:95",
  dc.sales_invoice     AS "Invoice:Link/Sales Invoice:140"
FROM `tabDelivery Challan` dc
LEFT JOIN `tabConstruction Site` cs ON cs.name = dc.construction_site
WHERE dc.docstatus = 1
ORDER BY dc.challan_date DESC, dc.dispatch_time DESC
""",
	},
	{
		"name": "Customer Order Status", "ref_doctype": "Concrete Order",
		"module": "RMC Dispatch",
		"query": """
SELECT
  co.customer          AS "Customer:Link/Customer:180",
  COUNT(co.name)       AS "Orders:Int:80",
  SUM(co.order_qty_m3) AS "Ordered m3:Float:110",
  SUM(co.delivered_qty_m3) AS "Delivered m3:Float:115",
  SUM(co.pending_qty_m3)   AS "Pending m3:Float:110",
  SUM(co.order_value)      AS "Order Value:Currency:140",
  SUM(CASE WHEN co.status IN ('Open','In Progress') THEN 1 ELSE 0 END) AS "Open Orders:Int:110"
FROM `tabConcrete Order` co
WHERE co.docstatus = 1
GROUP BY co.customer
ORDER BY SUM(co.order_value) DESC
""",
	},
	{
		"name": "Vehicle Utilisation and Trips", "ref_doctype": "Delivery Challan",
		"module": "RMC Dispatch",
		"query": """
SELECT
  dc.transit_mixer      AS "Vehicle:Link/Transit Mixer:120",
  tm.vehicle_type       AS "Type:Data:120",
  tm.capacity_m3        AS "Capacity m3:Float:110",
  COUNT(dc.name)        AS "Trips:Int:80",
  SUM(dc.qty_m3)        AS "Delivered m3:Float:120",
  SUM(dc.qty_m3)/NULLIF(COUNT(dc.name),0) AS "Avg Load m3:Float:115",
  AVG(dc.cycle_time_min) AS "Avg Cycle (min):Float:130",
  SUM(dc.distance_km)   AS "Distance km:Float:110",
  SUM(dc.amount)        AS "Revenue Carried:Currency:150"
FROM `tabDelivery Challan` dc
LEFT JOIN `tabTransit Mixer` tm ON tm.name = dc.transit_mixer
WHERE dc.docstatus = 1
GROUP BY dc.transit_mixer, tm.vehicle_type, tm.capacity_m3
ORDER BY COUNT(dc.name) DESC
""",
	},
	{
		"name": "Customer Wise Sales", "ref_doctype": "Delivery Challan",
		"module": "RMC Dispatch",
		"query": """
SELECT
  dc.customer      AS "Customer:Link/Customer:180",
  dc.grade         AS "Grade:Link/Concrete Grade:80",
  COUNT(dc.name)   AS "Loads:Int:80",
  SUM(dc.qty_m3)   AS "Qty m3:Float:110",
  AVG(dc.rate)     AS "Avg Rate:Currency:120",
  SUM(dc.amount)   AS "Value:Currency:140"
FROM `tabDelivery Challan` dc
WHERE dc.docstatus = 1
GROUP BY dc.customer, dc.grade
ORDER BY SUM(dc.amount) DESC
""",
	},
	{
		"name": "Cube Test Register", "ref_doctype": "Cube Test",
		"module": "RMC Production",
		"query": """
SELECT
  ct.name                 AS "Test:Link/Cube Test:110",
  ct.casting_date         AS "Cast On:Date:95",
  ct.testing_date         AS "Tested On:Date:100",
  ct.age_days             AS "Age (d):Data:70",
  ct.grade                AS "Grade:Link/Concrete Grade:75",
  ct.batch_production     AS "Batch:Link/Batch Production:130",
  ct.no_of_cubes          AS "Cubes:Int:70",
  ct.required_strength_mpa AS "Required MPa:Float:120",
  ct.avg_strength_mpa     AS "Achieved MPa:Float:120",
  ct.strength_pct         AS "Achieved %:Float:100",
  ct.result               AS "Result:Data:80",
  ct.tested_by            AS "Tested By:Data:120"
FROM `tabCube Test` ct
WHERE ct.docstatus = 1
ORDER BY ct.casting_date DESC, ct.name DESC
""",
	},
	{
		"name": "Plant Availability and Downtime", "ref_doctype": "Plant Status Log",
		"module": "RMC Plant Ops",
		"query": """
SELECT
  psl.log_date  AS "Date:Date:100",
  psl.plant     AS "Plant:Link/RMC Plant:220",
  SUM(CASE WHEN psl.status='Running'   THEN psl.duration_hours ELSE 0 END) AS "Running hrs:Float:110",
  SUM(CASE WHEN psl.status='Idle'      THEN psl.duration_hours ELSE 0 END) AS "Idle hrs:Float:95",
  SUM(CASE WHEN psl.status='Breakdown' THEN psl.duration_hours ELSE 0 END) AS "Breakdown hrs:Float:125",
  SUM(CASE WHEN psl.status='Stopped'   THEN psl.duration_hours ELSE 0 END) AS "Stopped hrs:Float:110",
  SUM(psl.duration_hours) AS "Logged hrs:Float:105",
  100 * SUM(CASE WHEN psl.status IN ('Running','Idle') THEN psl.duration_hours ELSE 0 END)
      / NULLIF(SUM(psl.duration_hours),0) AS "Availability %:Float:120"
FROM `tabPlant Status Log` psl
GROUP BY psl.log_date, psl.plant
ORDER BY psl.log_date DESC
""",
	},
	{
		"name": "Power and Diesel Consumption", "ref_doctype": "Power Log",
		"module": "RMC Plant Ops",
		"query": """
SELECT
  pl.log_date     AS "Date:Date:100",
  pl.plant        AS "Plant:Link/RMC Plant:220",
  pl.eb_units     AS "EB Units:Float:100",
  pl.eb_hours     AS "EB Hrs:Float:90",
  pl.dg_units     AS "DG Units:Float:100",
  pl.dg_hours     AS "DG Hrs:Float:90",
  pl.diesel_litres AS "Diesel L:Float:100",
  pl.diesel_cost  AS "Diesel Cost:Currency:120",
  (pl.eb_units + pl.dg_units) AS "Total Units:Float:110",
  pl.diesel_litres / NULLIF(pl.dg_units,0) AS "L per kWh:Float:100"
FROM `tabPower Log` pl
ORDER BY pl.log_date DESC
""",
	},
	{
		"name": "Breakdown and Maintenance Log", "ref_doctype": "Breakdown Log",
		"module": "RMC Plant Ops",
		"query": """
SELECT
  bd.name          AS "Breakdown:Link/Breakdown Log:120",
  bd.plant         AS "Plant:Link/RMC Plant:200",
  bd.equipment     AS "Equipment:Data:140",
  bd.reported_on   AS "Reported:Datetime:150",
  bd.resolved_on   AS "Resolved:Datetime:150",
  bd.downtime_hours AS "Downtime hrs:Float:120",
  bd.severity      AS "Severity:Data:90",
  bd.status        AS "Status:Data:90",
  bd.reason        AS "Reason:Data:240",
  bd.spare_cost    AS "Repair Cost:Currency:120"
FROM `tabBreakdown Log` bd
ORDER BY bd.reported_on DESC
""",
	},
]


def install():
	made, updated = [], []
	for r in REPORTS:
		if not frappe.db.exists("DocType", r["ref_doctype"]):
			continue
		if frappe.db.exists("Report", r["name"]):
			doc = frappe.get_doc("Report", r["name"])
			doc.query = r["query"]
			doc.ref_doctype = r["ref_doctype"]
			doc.module = r["module"]
			doc.save(ignore_permissions=True)
			updated.append(r["name"])
			continue
		frappe.get_doc({
			"doctype": "Report", "report_name": r["name"], "ref_doctype": r["ref_doctype"],
			"module": r["module"], "report_type": "Query Report", "is_standard": "Yes",
			"query": r["query"], "disabled": 0,
			"roles": [{"role": x} for x in
			          ("System Manager", "RMC Manager", "Plant Operator",
			           "Dispatch Incharge", "Quality Engineer", "RMC Accounts")
			          if frappe.db.exists("Role", x)],
		}).insert(ignore_permissions=True)
		made.append(r["name"])
	frappe.db.commit()
	print("  + reports created: %d, updated: %d" % (len(made), len(updated)))
	return {"created": made, "updated": updated}

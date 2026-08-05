"""
Code-first DocType generator for RMC Plant Management.

Run once with developer_mode = 1 so every DocType is materialised as a
version-controlled JSON file inside its module folder:

    bench --site rmc.local execute rmc.setup.build_doctypes.build

Idempotent: existing DocTypes are skipped, so it is safe to re-run after
adding a definition here.
"""

import frappe

MATERIAL_TYPES = "Cement\nSand\nAggregate\nFly Ash\nGGBS\nAdmixture\nWater\nOther"
SHIFTS = "Shift A\nShift B\nShift C"
VEHICLE_TYPES = "Transit Mixer\nConcrete Pump\nLoader\nTipper"

def _perms(submittable):
	"""Submit/cancel/amend flags are only legal on a submittable DocType —
	Frappe rejects the whole insert otherwise."""
	base = [
		{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1,
		 "report": 1, "export": 1, "print": 1, "email": 1, "share": 1},
		{"role": "RMC Manager", "read": 1, "write": 1, "create": 1, "delete": 1,
		 "report": 1, "export": 1, "print": 1, "email": 1, "share": 1},
		{"role": "Plant Operator", "read": 1, "write": 1, "create": 1,
		 "report": 1, "print": 1, "share": 1},
	]
	if submittable:
		for p in base:
			p["submit"] = 1
			if p["role"] != "Plant Operator":
				p["cancel"] = 1
				p["amend"] = 1
	return base


def F(fieldname, label, fieldtype, **kw):
	d = {"fieldname": fieldname, "label": label, "fieldtype": fieldtype}
	d.update(kw)
	return d


def SB(fieldname, label=""):
	return {"fieldname": fieldname, "label": label, "fieldtype": "Section Break"}


def CB(fieldname):
	return {"fieldname": fieldname, "fieldtype": "Column Break"}


# ---------------------------------------------------------------------------
# DocTypes in dependency order — a link target is always created before the
# doctype that points at it.
# ---------------------------------------------------------------------------
def doctypes():
	return [
		# =================== RMC Setup ===================
		{
			"name": "RMC Plant", "module": "RMC Setup",
			"autoname": "field:plant_name", "naming_rule": "By fieldname",
			"title_field": "plant_name",
			"fields": [
				F("plant_name", "Plant Name", "Data", reqd=1, unique=1, in_list_view=1),
				F("company", "Company", "Link", options="Company", reqd=1),
				F("location", "Location", "Data", in_list_view=1),
				F("capacity_m3_hr", "Capacity (m³/hr)", "Float", in_list_view=1,
				  description="Rated batching capacity — used for plant utilisation %."),
				F("commissioned_on", "Commissioned On", "Date"),
				CB("cb1"),
				F("store_warehouse", "Raw Material Warehouse", "Link", options="Warehouse",
				  description="Parent warehouse of the silos / yards feeding this plant."),
				F("finished_warehouse", "Finished Concrete Warehouse", "Link", options="Warehouse"),
				F("cost_center", "Cost Center", "Link", options="Cost Center"),
				F("is_active", "Is Active", "Check", default="1", in_list_view=1),
			],
		},
		{
			"name": "Concrete Grade", "module": "RMC Setup",
			"autoname": "field:grade", "naming_rule": "By fieldname",
			"title_field": "grade",
			"fields": [
				F("grade", "Grade", "Data", reqd=1, unique=1, in_list_view=1,
				  description="Standard IS grade designation, e.g. M25."),
				F("strength_mpa", "Characteristic Strength (MPa)", "Float", reqd=1, in_list_view=1),
				F("application", "Typical Application", "Data", in_list_view=1),
				CB("cb1"),
				F("item_code", "Concrete Item", "Link", options="Item", read_only=1,
				  description="Auto-created stock item this grade is produced and sold as."),
				F("default_rate", "Default Rate (₹/m³)", "Currency", in_list_view=1),
				F("is_active", "Is Active", "Check", default="1"),
			],
		},
		{
			"name": "Mix Design Item", "module": "RMC Setup", "istable": 1,
			"fields": [
				F("item_code", "Item", "Link", options="Item", reqd=1, in_list_view=1, columns=3),
				F("material_type", "Type", "Select", options=MATERIAL_TYPES, in_list_view=1, columns=2),
				F("qty_per_m3", "Qty / m³", "Float", reqd=1, in_list_view=1, columns=2, precision="3"),
				F("uom", "UOM", "Link", options="UOM", in_list_view=1, columns=1),
				F("rate", "Rate", "Currency", in_list_view=1, columns=2),
				F("amount", "Amount", "Currency", read_only=1, columns=2),
			],
		},
		{
			"name": "Mix Design", "module": "RMC Setup",
			"autoname": "format:MIX-{grade}-{####}", "title_field": "grade",
			"fields": [
				F("grade", "Concrete Grade", "Link", options="Concrete Grade", reqd=1, in_list_view=1),
				F("plant", "Plant", "Link", options="RMC Plant", in_list_view=1),
				F("design_version", "Version", "Data", default="1.0", in_list_view=1),
				F("effective_from", "Effective From", "Date", default="Today"),
				CB("cb1"),
				F("water_cement_ratio", "Water / Cement Ratio", "Float", precision="2"),
				F("slump_target_mm", "Target Slump (mm)", "Int", default="100"),
				F("is_active", "Is Active", "Check", default="1", in_list_view=1),
				F("approved_by", "Approved By", "Data"),
				SB("sb_items", "Materials per m³"),
				F("items", "Materials", "Table", options="Mix Design Item", reqd=1),
				F("total_weight_kg", "Total Weight (kg/m³)", "Float", read_only=1),
				F("cost_per_m3", "Material Cost (₹/m³)", "Currency", read_only=1),
				F("remarks", "Remarks", "Small Text"),
			],
		},
		{
			"name": "Transit Mixer", "module": "RMC Setup",
			"autoname": "field:vehicle_no", "naming_rule": "By fieldname",
			"title_field": "vehicle_no",
			"fields": [
				F("vehicle_no", "Vehicle No", "Data", reqd=1, unique=1, in_list_view=1),
				F("vehicle_type", "Vehicle Type", "Select", options=VEHICLE_TYPES,
				  default="Transit Mixer", reqd=1, in_list_view=1),
				F("capacity_m3", "Capacity (m³)", "Float", default="6", in_list_view=1),
				F("make", "Make / Model", "Data"),
				CB("cb1"),
				F("plant", "Plant", "Link", options="RMC Plant", in_list_view=1),
				F("ownership", "Ownership", "Select", options="Own\nHired", default="Own", in_list_view=1),
				F("default_driver", "Default Driver", "Link", options="Driver"),
				F("status", "Status", "Select",
				  options="Available\nOn Trip\nUnder Maintenance\nInactive",
				  default="Available", in_list_view=1),
				F("fitness_valid_upto", "Fitness Valid Upto", "Date"),
				F("insurance_valid_upto", "Insurance Valid Upto", "Date"),
			],
		},
		{
			"name": "Construction Site", "module": "RMC Setup",
			"autoname": "format:CS-{####}", "title_field": "site_name",
			"fields": [
				F("site_name", "Site Name", "Data", reqd=1, in_list_view=1),
				F("customer", "Customer", "Link", options="Customer", reqd=1, in_list_view=1),
				F("site_address", "Site Address", "Small Text", reqd=1),
				F("city", "City", "Data", in_list_view=1),
				CB("cb1"),
				F("distance_km", "Distance from Plant (km)", "Float", in_list_view=1,
				  description="Drives freight cost and expected trip cycle time."),
				F("contact_person", "Contact Person", "Data"),
				F("contact_no", "Contact No", "Data", in_list_view=1),
				F("pump_access", "Pump Access Available", "Check", default="1"),
				F("is_active", "Is Active", "Check", default="1"),
			],
		},
		{
			"name": "Silo", "module": "RMC Setup",
			"autoname": "field:silo_name", "naming_rule": "By fieldname",
			"title_field": "silo_name",
			"fields": [
				F("silo_name", "Silo / Yard Name", "Data", reqd=1, unique=1, in_list_view=1),
				F("plant", "Plant", "Link", options="RMC Plant", reqd=1, in_list_view=1),
				F("material_type", "Material Type", "Select", options=MATERIAL_TYPES,
				  reqd=1, in_list_view=1),
				F("item_code", "Item", "Link", options="Item", reqd=1, in_list_view=1),
				CB("cb1"),
				F("warehouse", "Warehouse", "Link", options="Warehouse", reqd=1,
				  description="Stock in this warehouse IS the silo level."),
				F("capacity_mt", "Capacity (MT / m³)", "Float", in_list_view=1),
				F("min_level_mt", "Low Level Alert At", "Float",
				  description="Below this the Low Stock alert fires on the dashboard."),
				F("is_active", "Is Active", "Check", default="1"),
			],
		},
		{
			"name": "RMC Settings", "module": "RMC Setup", "issingle": 1,
			"fields": [
				F("default_plant", "Default Plant", "Link", options="RMC Plant"),
				F("company", "Company", "Link", options="Company"),
				CB("cb1"),
				F("auto_create_sales_invoice", "Auto-create Sales Invoice on Challan", "Check",
				  default="1",
				  description="Submitting a Delivery Challan raises the sales invoice "
				              "(with stock update) so revenue and stock stay in step."),
				F("auto_stock_entry", "Auto Stock Entry on Batch Production", "Check", default="1"),
				SB("sb_alerts", "Alerts"),
				F("low_stock_alert", "Low Stock Alerts", "Check", default="1"),
				F("breakdown_alert", "Breakdown Alerts", "Check", default="1"),
				F("target_availability_pct", "Target Plant Availability %", "Percent", default="90"),
			],
		},
		# =================== RMC Materials ===================
		{
			"name": "Material Inward", "module": "RMC Materials", "is_submittable": 1,
			"autoname": "format:MI-{YY}{MM}-{#####}",
			"fields": [
				F("inward_date", "Inward Date", "Date", default="Today", reqd=1, in_list_view=1),
				F("inward_time", "Inward Time", "Time", default="05:00:00",
				  description="When the truck was weighed in. The stock receipt posts at this "
				              "moment, so material is in the silo before the shift consumes it."),
				F("plant", "Plant", "Link", options="RMC Plant", reqd=1),
				F("supplier", "Supplier", "Link", options="Supplier", reqd=1, in_list_view=1),
				F("supplier_dc_no", "Supplier DC / Invoice No", "Data"),
				CB("cb1"),
				F("item_code", "Item", "Link", options="Item", reqd=1, in_list_view=1),
				F("material_type", "Material Type", "Select", options=MATERIAL_TYPES, in_list_view=1),
				F("vehicle_no", "Vehicle No", "Data"),
				F("silo", "Silo / Yard", "Link", options="Silo",
				  description="Where the material is unloaded — sets the receiving warehouse."),
				SB("sb_wb", "Weighbridge"),
				F("gross_weight", "Gross Weight (MT)", "Float", precision="3"),
				F("tare_weight", "Tare Weight (MT)", "Float", precision="3"),
				CB("cb2"),
				F("net_weight", "Net Weight (MT)", "Float", precision="3", reqd=1, in_list_view=1,
				  description="Gross − Tare. Computed when both weights are entered."),
				F("uom", "UOM", "Link", options="UOM"),
				SB("sb_val", "Valuation"),
				F("rate", "Rate", "Currency", reqd=1),
				CB("cb3"),
				F("amount", "Amount", "Currency", read_only=1, in_list_view=1),
				SB("sb_qc", "Quality & Posting"),
				F("quality_ok", "Quality Accepted", "Check", default="1"),
				F("test_report", "Test Report No", "Data"),
				CB("cb4"),
				F("warehouse", "Warehouse", "Link", options="Warehouse", read_only=1),
				F("purchase_receipt", "Purchase Receipt", "Link", options="Purchase Receipt",
				  read_only=1, description="Auto-created on submit — this is what moves stock."),
				F("remarks", "Remarks", "Small Text"),
				F("amended_from", "Amended From", "Link", options="Material Inward",
				  read_only=1, print_hide=1, no_copy=1),
			],
		},
		# =================== RMC Production ===================
		{
			"name": "Batch Material", "module": "RMC Production", "istable": 1,
			"fields": [
				F("item_code", "Item", "Link", options="Item", reqd=1, in_list_view=1, columns=2),
				F("material_type", "Type", "Select", options=MATERIAL_TYPES, in_list_view=1, columns=1),
				F("target_qty", "Target Qty", "Float", in_list_view=1, columns=2, precision="3"),
				F("actual_qty", "Actual Qty", "Float", reqd=1, in_list_view=1, columns=2, precision="3"),
				F("uom", "UOM", "Link", options="UOM", columns=1),
				F("variance_pct", "Var %", "Float", read_only=1, in_list_view=1, columns=1, precision="2"),
				F("rate", "Rate", "Currency", columns=1),
				F("amount", "Amount", "Currency", read_only=1, columns=2),
				F("warehouse", "Source Warehouse", "Link", options="Warehouse"),
			],
		},
		{
			"name": "Batch Production", "module": "RMC Production", "is_submittable": 1,
			"autoname": "format:BP-{YY}{MM}-{#####}",
			"fields": [
				F("production_date", "Production Date", "Date", default="Today", reqd=1, in_list_view=1),
				F("plant", "Plant", "Link", options="RMC Plant", reqd=1),
				F("shift", "Shift", "Select", options=SHIFTS, default="Shift A", reqd=1, in_list_view=1),
				F("grade", "Concrete Grade", "Link", options="Concrete Grade", reqd=1, in_list_view=1),
				F("mix_design", "Mix Design", "Link", options="Mix Design", reqd=1),
				CB("cb1"),
				F("concrete_order", "Concrete Order", "Link", options="Concrete Order",
				  description="Order this pour belongs to — leave blank for stock production."),
				F("qty_m3", "Produced Qty (m³)", "Float", reqd=1, in_list_view=1, precision="2"),
				F("no_of_batches", "No of Batches", "Int", default="1"),
				F("start_time", "Start Time", "Datetime"),
				F("end_time", "End Time", "Datetime"),
				F("operator", "Batching Operator", "Data"),
				SB("sb_mat", "Material Consumption (target vs actual)"),
				F("materials", "Materials", "Table", options="Batch Material"),
				SB("sb_tot", "Totals"),
				F("total_material_cost", "Material Cost", "Currency", read_only=1),
				F("cost_per_m3", "Cost per m³", "Currency", read_only=1),
				CB("cb2"),
				F("stock_entry", "Stock Entry", "Link", options="Stock Entry", read_only=1,
				  description="Auto-created Manufacture entry: raw materials out, concrete in."),
				F("status", "Status", "Select", options="Draft\nProduced\nDispatched\nCancelled",
				  default="Draft", read_only=1, in_list_view=1),
				F("remarks", "Remarks", "Small Text"),
				F("amended_from", "Amended From", "Link", options="Batch Production",
				  read_only=1, print_hide=1, no_copy=1),
			],
		},
		{
			"name": "Cube Test", "module": "RMC Production", "is_submittable": 1,
			"autoname": "format:CT-{YY}{MM}-{####}",
			"fields": [
				F("batch_production", "Batch Production", "Link", options="Batch Production",
				  reqd=1, in_list_view=1),
				F("grade", "Grade", "Link", options="Concrete Grade", reqd=1, in_list_view=1),
				F("casting_date", "Casting Date", "Date", reqd=1, in_list_view=1),
				F("age_days", "Age (days)", "Select", options="7\n14\n28", default="28",
				  reqd=1, in_list_view=1),
				CB("cb1"),
				F("testing_date", "Testing Date", "Date"),
				F("no_of_cubes", "No of Cubes", "Int", default="3"),
				F("delivery_challan", "Delivery Challan", "Link", options="Delivery Challan"),
				F("tested_by", "Tested By", "Data"),
				SB("sb_res", "Result"),
				F("required_strength_mpa", "Required Strength (MPa)", "Float", read_only=1),
				F("avg_strength_mpa", "Achieved Strength (MPa)", "Float", reqd=1, in_list_view=1),
				CB("cb2"),
				F("strength_pct", "Achieved %", "Float", read_only=1, precision="1"),
				F("result", "Result", "Select", options="Pass\nFail", read_only=1, in_list_view=1),
				F("remarks", "Remarks", "Small Text"),
				F("amended_from", "Amended From", "Link", options="Cube Test",
				  read_only=1, print_hide=1, no_copy=1),
			],
		},
		# =================== RMC Dispatch ===================
		{
			"name": "Order Schedule", "module": "RMC Dispatch", "istable": 1,
			"fields": [
				F("schedule_date", "Date", "Date", reqd=1, in_list_view=1, columns=3),
				F("time_slot", "Time", "Data", in_list_view=1, columns=2),
				F("qty_m3", "Qty (m³)", "Float", reqd=1, in_list_view=1, columns=2),
				F("delivered_qty", "Delivered (m³)", "Float", read_only=1, in_list_view=1, columns=2),
				F("remarks", "Remarks", "Data", columns=3),
			],
		},
		{
			"name": "Concrete Order", "module": "RMC Dispatch", "is_submittable": 1,
			"autoname": "format:CO-{YY}{MM}-{####}",
			"fields": [
				F("customer", "Customer", "Link", options="Customer", reqd=1, in_list_view=1),
				F("construction_site", "Construction Site", "Link", options="Construction Site",
				  reqd=1, in_list_view=1),
				F("order_date", "Order Date", "Date", default="Today", reqd=1),
				F("grade", "Concrete Grade", "Link", options="Concrete Grade", reqd=1, in_list_view=1),
				CB("cb1"),
				F("order_qty_m3", "Ordered Qty (m³)", "Float", reqd=1, in_list_view=1),
				F("rate", "Rate (₹/m³)", "Currency", reqd=1),
				F("required_from", "Required From", "Date", reqd=1),
				F("required_to", "Required To", "Date"),
				F("pump_required", "Concrete Pump Required", "Check"),
				SB("sb_sch", "Pour Schedule"),
				F("schedule", "Schedule", "Table", options="Order Schedule"),
				SB("sb_prog", "Progress"),
				F("delivered_qty_m3", "Delivered Qty (m³)", "Float", read_only=1, in_list_view=1),
				F("pending_qty_m3", "Pending Qty (m³)", "Float", read_only=1),
				CB("cb2"),
				F("order_value", "Order Value", "Currency", read_only=1),
				F("status", "Status", "Select",
				  options="Open\nIn Progress\nCompleted\nClosed\nCancelled",
				  default="Open", read_only=1, in_list_view=1),
				F("site_engineer", "Site Engineer", "Data"),
				F("contact_no", "Contact No", "Data"),
				F("remarks", "Remarks", "Small Text"),
				F("amended_from", "Amended From", "Link", options="Concrete Order",
				  read_only=1, print_hide=1, no_copy=1),
			],
		},
		{
			"name": "Delivery Challan", "module": "RMC Dispatch", "is_submittable": 1,
			"autoname": "format:DC-{YY}{MM}-{#####}",
			"fields": [
				F("concrete_order", "Concrete Order", "Link", options="Concrete Order",
				  reqd=1, in_list_view=1),
				F("customer", "Customer", "Link", options="Customer", reqd=1, in_list_view=1),
				F("construction_site", "Construction Site", "Link", options="Construction Site", reqd=1),
				F("challan_date", "Challan Date", "Date", default="Today", reqd=1, in_list_view=1),
				CB("cb1"),
				F("grade", "Grade", "Link", options="Concrete Grade", reqd=1, in_list_view=1),
				F("qty_m3", "Qty (m³)", "Float", reqd=1, in_list_view=1, precision="2"),
				F("rate", "Rate (₹/m³)", "Currency"),
				F("amount", "Amount", "Currency", read_only=1),
				SB("sb_veh", "Vehicle & Trip"),
				F("transit_mixer", "Transit Mixer", "Link", options="Transit Mixer", reqd=1, in_list_view=1),
				F("driver", "Driver", "Link", options="Driver"),
				F("driver_name", "Driver Name", "Data", fetch_from="driver.full_name", read_only=1),
				F("batch_production", "Batch Production", "Link", options="Batch Production",
				  description="Load that filled this truck — links the challan back to its mix."),
				CB("cb2"),
				F("dispatch_time", "Dispatch Time", "Datetime", reqd=1),
				F("site_arrival_time", "Site Arrival Time", "Datetime"),
				F("unloading_end_time", "Unloading End Time", "Datetime"),
				F("return_time", "Plant Return Time", "Datetime"),
				F("cycle_time_min", "Cycle Time (min)", "Int", read_only=1,
				  description="Dispatch → plant return. The core RMC productivity number."),
				SB("sb_qc", "Quality at Site"),
				F("slump_mm", "Slump (mm)", "Int"),
				F("temperature_c", "Temperature (°C)", "Float"),
				CB("cb3"),
				F("cubes_taken", "Cubes Taken", "Check"),
				F("distance_km", "Distance (km)", "Float"),
				SB("sb_post", "Status & Posting"),
				F("status", "Status", "Select",
				  options="Dispatched\nDelivered\nReturned\nCancelled",
				  default="Dispatched", in_list_view=1),
				F("qr_code", "QR Code", "Data", read_only=1,
				  description="Printed on the challan for site-side verification."),
				CB("cb4"),
				F("sales_invoice", "Sales Invoice", "Link", options="Sales Invoice", read_only=1),
				F("received_by", "Received By", "Data"),
				F("customer_signature", "Customer Signature", "Attach Image", print_hide=1),
				F("remarks", "Remarks", "Small Text"),
				F("amended_from", "Amended From", "Link", options="Delivery Challan",
				  read_only=1, print_hide=1, no_copy=1),
			],
		},
		# =================== RMC Plant Ops ===================
		{
			"name": "Plant Status Log", "module": "RMC Plant Ops",
			"autoname": "format:PSL-{YY}{MM}-{#####}",
			"fields": [
				F("log_date", "Date", "Date", default="Today", reqd=1, in_list_view=1),
				F("plant", "Plant", "Link", options="RMC Plant", reqd=1),
				F("shift", "Shift", "Select", options=SHIFTS, reqd=1, in_list_view=1),
				F("status", "Status", "Select", options="Running\nIdle\nBreakdown\nStopped",
				  reqd=1, in_list_view=1),
				CB("cb1"),
				F("from_time", "From", "Datetime", reqd=1, in_list_view=1),
				F("to_time", "To", "Datetime", reqd=1),
				F("duration_hours", "Duration (hrs)", "Float", read_only=1, in_list_view=1, precision="2"),
				SB("sb_pwr", "Power"),
				F("power_source", "Power Source", "Select", options="EB\nDG\nNone", default="EB"),
				F("eb_voltage", "EB Voltage (V)", "Float"),
				CB("cb2"),
				F("dg_load_pct", "DG Load %", "Float"),
				F("reason", "Reason / Remarks", "Small Text"),
			],
		},
		{
			"name": "Breakdown Log", "module": "RMC Plant Ops",
			"autoname": "format:BD-{YY}{MM}-{####}",
			"fields": [
				F("plant", "Plant", "Link", options="RMC Plant", reqd=1, in_list_view=1),
				F("equipment", "Equipment", "Select",
				  options="Batching Plant\nMixer\nConveyor\nCement Silo\nWeighing System\n"
				          "Water System\nAir Compressor\nDG Set\nTransit Mixer\nConcrete Pump\nOther",
				  reqd=1, in_list_view=1),
				F("transit_mixer", "Transit Mixer", "Link", options="Transit Mixer",
				  depends_on="eval:doc.equipment=='Transit Mixer'"),
				F("reported_on", "Reported On", "Datetime", reqd=1, in_list_view=1),
				CB("cb1"),
				F("resolved_on", "Resolved On", "Datetime"),
				F("downtime_hours", "Downtime (hrs)", "Float", read_only=1, in_list_view=1, precision="2"),
				F("status", "Status", "Select", options="Open\nIn Progress\nClosed",
				  default="Open", in_list_view=1),
				F("severity", "Severity", "Select", options="Low\nMedium\nHigh", default="Medium"),
				SB("sb_det", "Details"),
				F("reason", "Reason", "Small Text", reqd=1),
				F("action_taken", "Action Taken", "Small Text"),
				F("attended_by", "Attended By", "Data"),
				F("spare_cost", "Spare / Repair Cost", "Currency"),
			],
		},
		{
			"name": "RMC Maintenance Task", "module": "RMC Plant Ops",
			"autoname": "format:MS-{####}",
			"fields": [
				F("equipment", "Equipment", "Data", reqd=1, in_list_view=1),
				F("plant", "Plant", "Link", options="RMC Plant", in_list_view=1),
				F("transit_mixer", "Transit Mixer", "Link", options="Transit Mixer"),
				F("frequency", "Frequency", "Select",
				  options="Daily\nWeekly\nFortnightly\nMonthly\nQuarterly\nHalf Yearly\nYearly",
				  reqd=1, in_list_view=1),
				CB("cb1"),
				F("last_done_on", "Last Done On", "Date"),
				F("next_due_on", "Next Due On", "Date", reqd=1, in_list_view=1),
				F("responsible", "Responsible", "Data"),
				F("status", "Status", "Select", options="Scheduled\nDue\nOverdue\nCompleted",
				  default="Scheduled", in_list_view=1),
				F("checklist", "Checklist / Scope", "Small Text"),
			],
		},
		{
			"name": "Power Log", "module": "RMC Plant Ops",
			"autoname": "format:PL-{YY}{MM}-{####}",
			"fields": [
				F("log_date", "Date", "Date", default="Today", reqd=1, unique=0, in_list_view=1),
				F("plant", "Plant", "Link", options="RMC Plant", reqd=1, in_list_view=1),
				CB("cb1"),
				F("eb_units", "EB Units (kWh)", "Float", in_list_view=1),
				F("eb_hours", "EB Hours", "Float"),
				SB("sb_dg", "DG Set"),
				F("dg_units", "DG Units (kWh)", "Float", in_list_view=1),
				F("dg_hours", "DG Hours", "Float"),
				CB("cb2"),
				F("diesel_litres", "Diesel Consumed (L)", "Float"),
				F("diesel_cost", "Diesel Cost", "Currency"),
				F("remarks", "Remarks", "Small Text"),
			],
		},
	]


def build():
	"""Create every DocType, order-independently.

	The definitions link both ways (Batch Production -> Concrete Order ->
	... -> Batch Production), so a single ordered pass can never satisfy every
	link target. Instead: try them all, defer the ones whose targets do not
	exist yet, and repeat while progress is being made.
	"""
	made, skipped, pending = [], [], []
	for dt in doctypes():
		if frappe.db.exists("DocType", dt["name"]):
			skipped.append(dt["name"])
		else:
			pending.append(dt)

	while pending:
		progressed = []
		errors = {}
		for dt in list(pending):
			try:
				_create(dt)
				made.append(dt["name"])
				progressed.append(dt)
			except Exception as e:
				errors[dt["name"]] = str(e).splitlines()[-1][:200]
		for dt in progressed:
			pending.remove(dt)
		if not progressed:
			frappe.db.rollback()
			raise RuntimeError("RMC: could not create %s -> %s"
			                   % ([d["name"] for d in pending], errors))

	frappe.db.commit()
	print("CREATED:", len(made), made)
	print("SKIPPED:", len(skipped), skipped)
	return {"created": made, "skipped": skipped}


def sync_fields():
	"""Add fields that exist in the spec but not yet on the live DocType.

	build() only creates whole DocTypes; once one is live, new fields added to
	the spec have to be pushed in separately. Existing fields are left alone.
	"""
	added = []
	for dt in doctypes():
		if not frappe.db.exists("DocType", dt["name"]):
			continue
		doc = frappe.get_doc("DocType", dt["name"])
		have = {f.fieldname for f in doc.fields}
		missing = [f for f in dt["fields"] if f["fieldname"] not in have]
		if not missing:
			continue
		for f in missing:
			doc.append("fields", f)
			added.append("%s.%s" % (dt["name"], f["fieldname"]))
		doc.save(ignore_permissions=True)
	frappe.db.commit()
	print("FIELDS ADDED:", added or "none")
	return added


def _create(dt):
	payload = {
		"doctype": "DocType",
		"name": dt["name"],
		"module": dt["module"],
		"custom": 0,
		"istable": dt.get("istable", 0),
		"issingle": dt.get("issingle", 0),
		"is_submittable": dt.get("is_submittable", 0),
		"editable_grid": 1,
		"track_changes": 1,
		"fields": dt["fields"],
		"permissions": [] if dt.get("istable") else _perms(dt.get("is_submittable", 0)),
	}
	for key in ("autoname", "naming_rule", "title_field"):
		if dt.get(key):
			payload[key] = dt[key]
	frappe.get_doc(payload).insert(ignore_permissions=True)

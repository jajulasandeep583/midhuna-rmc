"""Whitelisted endpoints behind the plant dashboard.

One call returns everything the "plant live status" strip needs, so the desk
page does not have to assemble it from a dozen list queries.
"""

import frappe
from frappe.utils import flt, getdate, nowdate, add_days


@frappe.whitelist()
def plant_status(plant=None):
	"""Live status card: what the plant is doing right now, and today's numbers."""
	plant = plant or frappe.db.get_single_value("RMC Settings", "default_plant")
	today = getdate(nowdate())

	last = frappe.get_all("Plant Status Log", filters={"plant": plant},
	                      fields=["status", "from_time", "to_time", "power_source",
	                              "eb_voltage", "dg_load_pct", "reason"],
	                      order_by="from_time desc", limit=1)
	current = last[0] if last else {}

	spans = frappe.db.sql("""
		SELECT status, SUM(duration_hours) hrs FROM `tabPlant Status Log`
		WHERE plant=%s AND log_date=%s GROUP BY status""", (plant, today), as_dict=True)
	hours = {s.status: flt(s.hrs) for s in spans}
	logged = sum(hours.values())
	uptime = hours.get("Running", 0) + hours.get("Idle", 0)

	produced = flt(frappe.db.sql("""SELECT SUM(qty_m3) FROM `tabBatch Production`
	                                WHERE docstatus=1 AND production_date=%s""",
	                             today)[0][0])
	dispatched = frappe.db.sql("""SELECT COUNT(*), SUM(qty_m3), SUM(amount)
	                              FROM `tabDelivery Challan`
	                              WHERE docstatus=1 AND challan_date=%s""", today)[0]

	return {
		"plant": plant,
		"status": current.get("status") or "No log today",
		"since": current.get("from_time"),
		"power_source": current.get("power_source"),
		"eb_voltage": current.get("eb_voltage"),
		"dg_load_pct": current.get("dg_load_pct"),
		"running_hours": round(hours.get("Running", 0), 2),
		"idle_hours": round(hours.get("Idle", 0), 2),
		"breakdown_hours": round(hours.get("Breakdown", 0), 2),
		"availability_pct": round(100.0 * uptime / logged, 1) if logged else 0,
		"today_production_m3": round(produced, 2),
		"today_trips": dispatched[0] or 0,
		"today_dispatch_m3": round(flt(dispatched[1]), 2),
		"today_dispatch_value": round(flt(dispatched[2]), 2),
		"open_breakdowns": frappe.db.count("Breakdown Log",
		                                   {"status": ["in", ["Open", "In Progress"]]}),
		"mixers_available": frappe.db.count("Transit Mixer", {"status": "Available"}),
		"mixers_on_trip": frappe.db.count("Transit Mixer", {"status": "On Trip"}),
	}


@frappe.whitelist()
def silo_levels():
	"""Every silo with its live level — the material-stock panel."""
	out = []
	for s in frappe.get_all("Silo", filters={"is_active": 1},
	                        fields=["name", "silo_name", "material_type", "item_code",
	                                "warehouse", "capacity_mt", "min_level_mt"],
	                        order_by="material_type, silo_name"):
		qty = flt(frappe.db.get_value("Bin", {"item_code": s.item_code,
		                                      "warehouse": s.warehouse}, "actual_qty")) / 1000.0
		pct = round(100.0 * qty / flt(s.capacity_mt), 1) if flt(s.capacity_mt) else 0
		out.append({
			"silo": s.silo_name, "material": s.material_type, "item": s.item_code,
			"stock_mt": round(qty, 2), "capacity_mt": s.capacity_mt, "filled_pct": pct,
			"low": bool(s.min_level_mt and qty <= flt(s.min_level_mt)),
		})
	return out


@frappe.whitelist()
def order_book():
	"""Orders still owed to customers, most urgent first."""
	return frappe.db.sql("""
		SELECT co.name, co.customer, cs.site_name, co.grade, co.order_qty_m3,
		       co.delivered_qty_m3, co.pending_qty_m3, co.required_from, co.status
		FROM `tabConcrete Order` co
		LEFT JOIN `tabConstruction Site` cs ON cs.name = co.construction_site
		WHERE co.docstatus=1 AND co.status IN ('Open','In Progress')
		ORDER BY co.required_from ASC, co.pending_qty_m3 DESC
		LIMIT 50""", as_dict=True)


@frappe.whitelist()
def production_trend(days=14):
	"""Daily produced vs dispatched m³ for the trend chart."""
	days = int(days)
	start = add_days(getdate(nowdate()), -(days - 1))
	prod = frappe.db.sql("""SELECT production_date d, SUM(qty_m3) q
	                        FROM `tabBatch Production`
	                        WHERE docstatus=1 AND production_date >= %s
	                        GROUP BY production_date""", start, as_dict=True)
	disp = frappe.db.sql("""SELECT challan_date d, SUM(qty_m3) q
	                        FROM `tabDelivery Challan`
	                        WHERE docstatus=1 AND challan_date >= %s
	                        GROUP BY challan_date""", start, as_dict=True)
	pmap = {str(r.d): flt(r.q) for r in prod}
	dmap = {str(r.d): flt(r.q) for r in disp}
	out = []
	for i in range(days):
		d = str(add_days(start, i))
		out.append({"date": d, "produced": round(pmap.get(d, 0), 2),
		            "dispatched": round(dmap.get(d, 0), 2)})
	return out

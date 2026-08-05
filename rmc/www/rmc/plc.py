"""Public live-PLC page — one plant at a time, refreshing itself.

This is the screen you put on the plant office wall. It reads the same tag
feed the desk does; nothing is stored twice.
"""

import frappe
from frappe.utils import flt, get_datetime, now_datetime

from rmc import plc
from rmc.www.rmc.index import common

no_cache = 1


def get_context(context):
	common(context)
	context.title = "Live Plant Signals"

	context.plants = plc.plants()
	selected = frappe.form_dict.get("plant")
	if not selected or not any(p.name == selected for p in context.plants):
		selected = context.plants[0].name if context.plants else None
	context.selected_plant = selected
	context.plant_row = next((p for p in context.plants if p.name == selected), None)

	rows = plc.live(selected) if selected else []
	context.tags = rows
	context.alarms = [r for r in rows if r.get("alarm")]
	context.stale = [r for r in rows if r.get("stale")]

	groups = {}
	for r in rows:
		groups.setdefault(r.category, []).append(r)
	context.groups = [(c, groups[c]) for c in plc.CATEGORY_ORDER if c in groups]

	status = next((r for r in rows if r.tag_code == "PLANT_RUN"), None)
	context.running = bool(status and flt(status.value) >= 1)
	context.last_seen = max([get_datetime(r.reading_time) for r in rows if r.reading_time],
	                        default=None)
	context.last_seen_h = context.last_seen.strftime("%d %b %Y, %H:%M") if context.last_seen else "—"

	# a 24-hour trace for the four signals an operator actually watches
	watch = ["PLANT_KW", "MIXER_CURRENT", "CEM_SILO1_LVL", "EB_VOLTAGE"]
	context.traces = []
	for code in watch:
		tag = next((r for r in rows if r.tag_code == code), None)
		if not tag:
			continue
		points = plc.trend(tag.name, 24)
		if not points:
			continue
		vals = [flt(p.value) for p in points]
		peak = max(vals) or 1
		context.traces.append({
			"name": tag.tag_name, "unit": tag.unit,
			"now": tag.value, "peak": round(peak, 1),
			"bars": [round(100.0 * v / peak, 1) for v in vals][-96:],
		})

	context.reading_count = frappe.db.count("RMC PLC Reading", {"plant": selected}) if selected else 0

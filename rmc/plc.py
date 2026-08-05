"""The plant's PLC feed, landing in ERP 24/7.

A batching plant's PLC already knows the silo levels, the weigh-hopper loads,
the mixer motor current and the incoming supply. This module is the ERP side of
that link: one tag master per signal per plant, a reading per poll, and a
simulator that stands in for the real OPC/Modbus bridge until it is wired.

Each plant is a separate feed — tags carry the plant, readings carry the plant,
and every screen filters by it, so two plants never blur into one.

    bench --site rmc.local execute rmc.plc.install_tags
    bench --site rmc.local execute rmc.plc.simulate_history
    bench --site rmc.local execute rmc.plc.poll          # scheduled every 15 min
"""

import math
import random

import frappe
from frappe.utils import add_to_date, flt, get_datetime, now_datetime

# (tag code, name, category, unit, min, max, warn low, warn high, order)
TAGS = [
	("CEM_SILO1_LVL", "Cement Silo 1 Level", "Silo Level", "%", 0, 100, 15, None, 10),
	("CEM_SILO2_LVL", "Cement Silo 2 Level", "Silo Level", "%", 0, 100, 15, None, 11),
	("FLYASH_LVL", "Fly Ash Silo Level", "Silo Level", "%", 0, 100, 15, None, 12),
	("AGG20_LVL", "Aggregate 20mm Bin", "Silo Level", "%", 0, 100, 20, None, 13),
	("AGG10_LVL", "Aggregate 10mm Bin", "Silo Level", "%", 0, 100, 20, None, 14),
	("SAND_LVL", "Sand Bin Level", "Silo Level", "%", 0, 100, 20, None, 15),
	("WATER_TANK_LVL", "Water Tank Level", "Silo Level", "%", 0, 100, 25, None, 16),
	("ADMIX_TANK_LVL", "Admixture Tank Level", "Silo Level", "%", 0, 100, 20, None, 17),

	("CEM_WEIGH", "Cement Weigh Hopper", "Weigh Hopper", "kg", 0, 600, None, 560, 20),
	("AGG_WEIGH", "Aggregate Weigh Hopper", "Weigh Hopper", "kg", 0, 4000, None, 3800, 21),
	("WATER_WEIGH", "Water Weigh Hopper", "Weigh Hopper", "L", 0, 300, None, 285, 22),
	("ADMIX_WEIGH", "Admixture Dosing", "Weigh Hopper", "L", 0, 15, None, 14, 23),

	("MIXER_CURRENT", "Mixer Motor Current", "Motor", "A", 0, 120, None, 105, 30),
	("MIXER_RPM", "Mixer Drum Speed", "Motor", "rpm", 0, 40, 12, 38, 31),
	("CONV_CURRENT", "Aggregate Conveyor Current", "Motor", "A", 0, 60, None, 52, 32),
	("SCREW_CURRENT", "Cement Screw Current", "Motor", "A", 0, 45, None, 40, 33),

	("AIR_PRESSURE", "Compressed Air Pressure", "Process", "bar", 0, 10, 5.5, 9, 40),
	("MIX_TIME", "Mixing Cycle Time", "Process", "s", 0, 120, None, 95, 41),
	("SLUMP_EST", "Estimated Slump", "Process", "mm", 0, 220, 80, 170, 42),
	("MOISTURE_SAND", "Sand Moisture Probe", "Process", "%", 0, 12, None, 8, 43),

	("EB_VOLTAGE", "EB Supply Voltage", "Power", "V", 0, 480, 390, 440, 50),
	("EB_CURRENT", "EB Line Current", "Power", "A", 0, 400, None, 350, 51),
	("PLANT_KW", "Plant Load", "Power", "kW", 0, 250, None, 220, 52),
	("POWER_FACTOR", "Power Factor", "Power", "", 0, 1, 0.85, None, 53),
	("DG_LOAD", "DG Set Load", "Power", "%", 0, 100, None, 85, 54),

	("BATCH_COUNT", "Batches Since Midnight", "Counter", "nos", 0, 400, None, None, 60),
	("PROD_TODAY", "Produced Today", "Counter", "m3", 0, 600, None, None, 61),
	("PLANT_RUN", "Plant Running", "Status", "0/1", 0, 1, None, None, 70),
	("AUTO_MODE", "Auto Mode Selected", "Status", "0/1", 0, 1, None, None, 71),
]

CATEGORY_ORDER = ["Status", "Silo Level", "Weigh Hopper", "Motor", "Process", "Power", "Counter"]


def plant_code(plant):
	"""VSKP from 'Midhuna RMC Plant - Visakhapatnam' — short, stable, per plant."""
	tail = plant.split("-")[-1].strip()
	letters = [c for c in tail.upper() if c.isalpha()]
	return "".join(letters[:4]) or "PLNT"


def install_tags():
	"""Every active plant gets the full tag set. Idempotent."""
	made = 0
	for plant in frappe.get_all("RMC Plant", filters={"is_active": 1}, pluck="name"):
		code = plant_code(plant)
		for tag_code, name, cat, unit, lo, hi, wlo, whi, order in TAGS:
			key = "TAG-%s-%s" % (code, tag_code)
			if frappe.db.exists("RMC PLC Tag", key):
				continue
			frappe.get_doc({
				"doctype": "RMC PLC Tag", "tag_name": name, "tag_code": tag_code,
				"plant": plant, "plant_code": code, "category": cat, "unit": unit,
				"min_value": lo, "max_value": hi, "warn_low": wlo, "warn_high": whi,
				"display_order": order, "is_active": 1,
			}).insert(ignore_permissions=True)
			made += 1
	frappe.db.commit()
	print("  + PLC tags created: %d (%d plants x %d tags)"
	      % (made, frappe.db.count("RMC Plant", {"is_active": 1}), len(TAGS)))
	return made


# ---------------------------------------------------------------- the signal
def _value(tag_code, lo, hi, when, seed):
	"""A believable value for this tag at this moment.

	Deterministic per tag and timestamp, so the same minute always reads the
	same — a simulator that jitters randomly on every refresh looks broken.
	"""
	rng = random.Random("%s|%s|%s" % (tag_code, when.strftime("%Y%m%d%H%M"), seed))
	hour = when.hour + when.minute / 60.0
	# the plant works 06:00-20:00; outside that it idles
	running = 6 <= hour <= 20 and when.weekday() != 6
	day_curve = math.sin((hour - 6) / 14.0 * math.pi) if running else 0

	if tag_code.endswith("_LVL"):
		# silos drain through the day and get topped up overnight
		base = 88 - 55 * (0 if not running else (hour - 6) / 14.0)
		return max(8.0, min(98.0, base + rng.uniform(-4, 4)))
	if tag_code == "PLANT_RUN":
		return 1 if running else 0
	if tag_code == "AUTO_MODE":
		return 1 if running else 0
	if tag_code == "BATCH_COUNT":
		return round(max(0, 42 * day_curve + rng.uniform(-2, 2)) if running else 0)
	if tag_code == "PROD_TODAY":
		return round(max(0, 95 * ((hour - 6) / 14.0) + rng.uniform(-3, 3)) if running else 0, 1)
	if not running:
		# idle: motors off, supply still there
		if tag_code.startswith("EB_") or tag_code == "POWER_FACTOR":
			return round(rng.uniform(408, 424) if tag_code == "EB_VOLTAGE"
			             else (rng.uniform(0.92, 0.98) if tag_code == "POWER_FACTOR"
			                   else rng.uniform(2, 8)), 2)
		return round(rng.uniform(0, 1.5), 2)

	mid = (flt(lo) + flt(hi)) / 2.0
	spread = (flt(hi) - flt(lo)) / 2.0
	if tag_code in ("EB_VOLTAGE",):
		return round(rng.uniform(405, 428), 1)
	if tag_code == "POWER_FACTOR":
		return round(rng.uniform(0.88, 0.98), 3)
	if tag_code == "MOISTURE_SAND":
		return round(rng.uniform(2.5, 6.5), 2)
	if tag_code == "AIR_PRESSURE":
		return round(rng.uniform(6.2, 8.4), 2)
	if tag_code == "SLUMP_EST":
		return round(rng.uniform(95, 145), 0)
	if tag_code == "MIX_TIME":
		return round(rng.uniform(45, 75), 0)
	if tag_code == "DG_LOAD":
		return round(rng.uniform(0, 12), 1)
	# weigh hoppers and motors swing with the batching cycle
	return round(max(0.0, mid * (0.55 + 0.45 * day_curve) + rng.uniform(-spread * 0.12,
	                                                                   spread * 0.12)), 2)


def _write(tag, when, seed=0):
	value = _value(tag.tag_code, tag.min_value, tag.max_value, when, seed)
	quality = "Good" if random.Random(str(when) + tag.name).random() > 0.004 else "Uncertain"
	doc = frappe.get_doc({
		"doctype": "RMC PLC Reading", "plant": tag.plant, "tag": tag.name,
		"reading_time": when, "value": value, "unit": tag.unit, "quality": quality,
	})
	doc.flags.ignore_permissions = True
	doc.insert()
	return value


def poll():
	"""Scheduled: take one reading of every active tag, right now."""
	now = now_datetime().replace(second=0, microsecond=0)
	n = 0
	for tag in frappe.get_all("RMC PLC Tag", filters={"is_active": 1},
	                          fields=["name", "plant", "tag_code", "unit",
	                                  "min_value", "max_value"]):
		_write(frappe._dict(tag), now)
		n += 1
	frappe.db.commit()
	return n


def simulate_history(hours=24, every_minutes=15):
	"""Backfill so the trend lines have something to show from the first minute."""
	hours = int(hours)
	every_minutes = int(every_minutes)
	now = now_datetime().replace(second=0, microsecond=0)
	start = add_to_date(now, hours=-hours)
	tags = [frappe._dict(t) for t in frappe.get_all(
		"RMC PLC Tag", filters={"is_active": 1},
		fields=["name", "plant", "tag_code", "unit", "min_value", "max_value"])]

	if not tags:
		install_tags()
		return simulate_history(hours, every_minutes)

	written = 0
	when = start
	while when <= now:
		if not frappe.db.exists("RMC PLC Reading", {"tag": tags[0].name, "reading_time": when}):
			for t in tags:
				_write(t, when)
				written += 1
		when = add_to_date(when, minutes=every_minutes)
	frappe.db.commit()
	print("  + PLC readings written: %d (%d tags x %d hours)" % (written, len(tags), hours))
	return written


def purge(days=7):
	"""Keep the feed from growing without bound."""
	cutoff = add_to_date(now_datetime(), days=-int(days))
	frappe.db.sql("DELETE FROM `tabRMC PLC Reading` WHERE reading_time < %s", cutoff)
	frappe.db.commit()


# ---------------------------------------------------------------- read side
@frappe.whitelist()
def live(plant=None):
	"""Latest reading of every tag for one plant, ready to draw."""
	plant = plant or frappe.db.get_single_value("RMC Settings", "default_plant")
	rows = frappe.db.sql("""
		SELECT t.name, t.tag_name, t.tag_code, t.category, t.unit, t.min_value, t.max_value,
		       t.warn_low, t.warn_high, t.display_order,
		       r.value, r.reading_time, r.quality
		FROM `tabRMC PLC Tag` t
		LEFT JOIN `tabRMC PLC Reading` r ON r.name = (
			SELECT r2.name FROM `tabRMC PLC Reading` r2
			WHERE r2.tag = t.name ORDER BY r2.reading_time DESC LIMIT 1)
		WHERE t.is_active = 1 AND t.plant = %s
		ORDER BY t.display_order, t.tag_name""", plant, as_dict=True)

	for r in rows:
		span = flt(r.max_value) - flt(r.min_value)
		r["pct"] = round(100.0 * (flt(r.value) - flt(r.min_value)) / span, 1) if span else 0
		r["alarm"] = bool(
			(r.warn_low is not None and flt(r.warn_low) and flt(r.value) < flt(r.warn_low))
			or (r.warn_high is not None and flt(r.warn_high) and flt(r.value) > flt(r.warn_high)))
		r["stale"] = (not r.reading_time) or (
			(now_datetime() - get_datetime(r.reading_time)).total_seconds() > 3600)
	return rows


@frappe.whitelist()
def trend(tag, hours=24):
	return frappe.db.sql("""
		SELECT reading_time, value FROM `tabRMC PLC Reading`
		WHERE tag = %s AND reading_time >= %s ORDER BY reading_time""",
		(tag, add_to_date(now_datetime(), hours=-int(hours))), as_dict=True)


@frappe.whitelist()
def plants():
	return frappe.get_all("RMC Plant", filters={"is_active": 1},
	                      fields=["name", "location", "capacity_m3_hr"], order_by="name")

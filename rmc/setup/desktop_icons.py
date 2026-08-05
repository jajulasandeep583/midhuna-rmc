"""Workspace header icons — the tiles on the /apps desk screen.

Frappe's sidebar_header.set_header_icon() assigns the Workspace Sidebar's
header_icon and then immediately overwrites it with a generated letter tile, so
that field never reaches the screen. The only path that renders a real image is
a Desktop Icon whose label matches the sidebar title, backed by a file at
  <app>/public/icons/desktop_icons/{solid,subtle}/<scrub(label)>.svg
which frappe indexes into boot.desktop_icon_urls.

So each workspace gets a proper 54x54 tile, generated from the same glyph
geometry as the sprite so the desk and the tile always agree.
"""

import os
import re

import frappe

# workspace -> (sprite symbol, tile colour)
TILES = {
	"RMC Dashboard": ("rmc-dashboard", "#1E40AF"),
	"RMC Production": ("rmc-batch", "#16A34A"),
	"RMC Materials": ("rmc-silo", "#B45309"),
	"RMC Dispatch": ("rmc-dispatch", "#9333EA"),
	"RMC Quality": ("rmc-quality", "#15803D"),
	"RMC Setup": ("rmc-settings", "#475569"),
}

# the rounded square erpnext uses, so our tiles sit in the same grid
SQUIRCLE = ("M38.5714 0H15.4286C6.90761 0 0 6.90761 0 15.4286V38.5714C0 47.0924 6.90761 54 "
            "15.4286 54H38.5714C47.0924 54 54 47.0924 54 38.5714V15.4286C54 6.90761 47.0924 0 "
            "38.5714 0Z")

SCALE = 1.45          # 24 -> 34.8 within a 54 canvas
OFFSET = (54 - 24 * SCALE) / 2


def glyphs():
	"""Pull each symbol's inner geometry straight out of the sprite."""
	path = frappe.get_app_path("rmc", "public", "icons", "rmc-icons.svg")
	src = open(path, encoding="utf-8").read()
	out = {}
	for m in re.finditer(r'<symbol[^>]*id="icon-(rmc-[a-z0-9-]+)"[^>]*>(.*?)</symbol>',
	                     src, re.S):
		out[m.group(1)] = m.group(2).strip()
	return out


def tile(inner, colour, solid):
	bg = ('<path d="%s" fill="%s"/>' % (SQUIRCLE, colour) if solid
	      else '<path d="%s" fill="%s" fill-opacity="0.12"/>' % (SQUIRCLE, colour))
	stroke = "#FFFFFF" if solid else colour
	return (
		'<svg width="54" height="54" viewBox="0 0 54 54" fill="none" '
		'xmlns="http://www.w3.org/2000/svg">\n'
		"%s\n"
		'<g transform="translate(%.2f %.2f) scale(%s)" fill="none" '
		'stroke="%s" stroke-width="1.9" stroke-linecap="round" '
		'stroke-linejoin="round">\n%s\n</g>\n</svg>\n'
		% (bg, OFFSET, OFFSET, SCALE, stroke, inner)
	)


def write_tile_files():
	"""Regenerate the tile SVGs from the sprite.

	The generated files are COMMITTED, so a deployed site never needs this to
	run — which matters where the app tree is read-only at runtime. Failures
	are swallowed on purpose: they must never abort the rest of setup, or the
	Desktop Icon records go missing and the desk falls back to letter tiles.
	"""
	written = 0
	try:
		g = glyphs()
		base = frappe.get_app_path("rmc", "public", "icons", "desktop_icons")
		for variant in ("solid", "subtle"):
			os.makedirs(os.path.join(base, variant), exist_ok=True)
		for label, (symbol, colour) in TILES.items():
			inner = g.get(symbol)
			if not inner:
				print("  ! no glyph for %s" % symbol)
				continue
			fname = frappe.scrub(label) + ".svg"
			for variant, solid in (("solid", True), ("subtle", False)):
				target = os.path.join(base, variant, fname)
				content = tile(inner, colour, solid)
				if os.path.exists(target) and open(target, encoding="utf-8").read() == content:
					continue
				with open(target, "w", encoding="utf-8") as fh:
					fh.write(content)
				written += 1
	except OSError as e:
		print("  ! app tree not writable (%s) - keeping the committed tile files" % e)
		return
	print("  + desktop icon files refreshed: %d" % written)


def install():
	# Records first, files last: the records are what make the tiles render,
	# and the file write may legitimately fail on a read-only app tree.
	for label, (symbol, colour) in TILES.items():
		if not frappe.db.exists("Workspace", label):
			continue
		name = frappe.db.get_value("Desktop Icon", {"label": label})
		doc = (frappe.get_doc("Desktop Icon", name) if name
		       else frappe.new_doc("Desktop Icon"))
		if not name:
			doc.label = label
		doc.app = "rmc"
		doc.icon = symbol
		doc.icon_type = "Link"
		doc.standard = 1
		doc.hidden = 0
		# Each workspace stands on its own on the desk. Nested under the app
		# tile they do not appear there at all.
		doc.parent_icon = None
		# Link through the Workspace Sidebar, never as "External": v16 prefixes
		# an External icon's link with the origin and then opens it in a NEW TAB,
		# and drops it from the app-switcher menu.
		doc.link = None
		if frappe.db.exists("Workspace Sidebar", label):
			doc.link_type = "Workspace Sidebar"
			doc.link_to = label
			doc.sidebar = label
		doc.flags.ignore_permissions = True
		doc.save()

	# frappe generates an "App"-type icon for every installed app from the
	# add_to_apps_screen hook, always link_type External — which opens in a new
	# tab. Ours duplicates the RMC Dashboard tile, so hide it.
	if frappe.db.exists("Desktop Icon", {"label": "RMC Plant Management",
	                                     "icon_type": "App"}):
		frappe.db.set_value("Desktop Icon",
		                    {"label": "RMC Plant Management", "icon_type": "App"},
		                    "hidden", 1)

	frappe.db.commit()
	frappe.clear_cache()
	print("  + desktop icon records: %d" % len(TILES))

	write_tile_files()


run = install

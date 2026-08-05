"""A Custom HTML Block of big navigation tiles, pinned to the top of every
RMC workspace.

Frappe renders a Custom HTML Block inside a **shadow root**, so neither the
icon sprite (`<use href="#icon-...">` cannot cross the boundary) nor the desk
stylesheet reaches it. Every icon is therefore inlined with its own stroke, and
the tiles are plain anchors so no script is needed either.
"""

import json

import frappe

BLOCK = "RMC Navigator"

# geometry lifted from public/icons/rmc-icons.svg so the tiles match the sprite
GLYPHS = {
	"manage": '<path d="M3 3h8v6H3zM13 3h8v10h-8zM3 11h8v10H3zM13 15h8v6h-8z"/>',
	"tower": '<path d="M4 18a8 8 0 1 1 16 0"/><path d="M12 18l4.5-4.5"/><path d="M4 18h3M17 18h3"/>',
	"batch": '<ellipse cx="12" cy="12" rx="7" ry="6"/><path d="M7 9l10 6M7 15l10-6"/>'
	         '<path d="M12 2v2M12 20v2"/>',
	"dispatch": '<path d="M3 16V8h9v8"/><path d="M12 11h4l3 3v2h-7"/>'
	            '<circle cx="7" cy="18" r="1.8"/><circle cx="16" cy="18" r="1.8"/>'
	            '<path d="M7.5 8V4M5.5 5.5 7.5 3.5 9.5 5.5"/>',
	"silo": '<path d="M7 8h10v9H7z"/><path d="M7 8 12 3l5 5"/><path d="M10 17v4h4v-4"/>'
	        '<path d="M7 11h10M7 14h10"/>',
	"quality": '<path d="M12 3l7 3v6c0 4.4-3 8-7 9-4-1-7-4.6-7-9V6z"/>'
	           '<path d="M9 12l2.2 2.2L15.5 10"/>',
	"order": '<path d="M9 3h6v3H9z"/><path d="M15 4.5h3V21H6V4.5h3"/><path d="M9 13l2 2 4-4"/>',
	"report": '<path d="M4 21V4"/><path d="M4 21h17"/><path d="M8 17V11M13 17V6M18 17v-8"/>',
	"plc": '<rect x="2.5" y="5" width="19" height="14" rx="2"/>'
	       '<path d="M5.5 13l2.5-3.5L10.5 15l2-6 2 4.5 1.5-2h2.5"/>'
	       '<path d="M6 2.5v2.5M12 2.5v2.5M18 2.5v2.5"/>',
	"web": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/>'
	       '<path d="M12 3c2.6 2.6 4 5.7 4 9s-1.4 6.4-4 9c-2.6-2.6-4-5.7-4-9s1.4-6.4 4-9z"/>',
	"guide": '<path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v16H6.5A2.5 2.5 0 0 0 4 20.5z"/>'
	         '<path d="M4 4.5v16A2.5 2.5 0 0 0 6.5 23H20v-5"/><path d="M8 7h8M8 11h6"/>',
	"settings": '<circle cx="12" cy="12" r="3"/>'
	            '<path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3'
	            'M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/>',
}

# (label, sub-label, route, glyph, colour)
TILES = [
	("Management", "Sales, stock, purchase — one view", "/app/rmc-manage", "manage", "#1E40AF"),
	("Control Tower", "Today, trends and alerts", "/app/rmc-control-tower", "tower", "#0F766E"),
	("Batching", "Batch the concrete", "/app/rmc-batch-board", "batch", "#16A34A"),
	("Dispatch", "Trips, trucks, challans", "/app/rmc-dispatch-board", "dispatch", "#9333EA"),
	("Silo & Stock", "Levels and days of cover", "/app/rmc-silo-board", "silo", "#B45309"),
	("Quality", "Cube tests and slump", "/app/rmc-quality-board", "quality", "#15803D"),
	("Order 360", "One order end to end", "/app/rmc-order-360", "order", "#DB2777"),
	("Live PLC", "Plant signals, 24/7", "/app/rmc-plc-board", "plc", "#0EA5E9"),
	("Web Pages", "Public plant dashboards", "/rmc", "web", "#2563EB"),
	("Reports", "Every MIS report", "/app/rmc-reports", "report", "#6D28D9"),
	("How to Use", "The full guide", "/app/rmc-guide", "guide", "#BE185D"),
]

STYLE = """
.rmcnav{display:grid;grid-template-columns:repeat(auto-fit,minmax(178px,1fr));gap:12px;
	margin:2px 0 6px}
.rmcnav a{display:flex;gap:11px;align-items:flex-start;text-decoration:none;
	border:1px solid rgba(125,140,155,.28);border-radius:12px;padding:13px 14px;
	background:rgba(255,255,255,.02);transition:transform .12s ease,box-shadow .12s ease,
	border-color .12s ease}
.rmcnav a:hover{transform:translateY(-2px);box-shadow:0 6px 18px rgba(15,30,50,.13);
	border-color:rgba(125,140,155,.5)}
.rmcnav .ic{flex:none;width:38px;height:38px;border-radius:10px;display:grid;place-items:center}
.rmcnav .ic svg{width:22px;height:22px}
.rmcnav .tx{min-width:0}
.rmcnav .t{font-size:13.5px;font-weight:750;line-height:1.25;color:inherit}
.rmcnav .s{font-size:11.5px;opacity:.68;line-height:1.3;margin-top:2px}
"""


def html():
	out = ['<div class="rmcnav">']
	for label, sub, route, glyph, colour in TILES:
		out.append(
			'<a href="%s"><span class="ic" style="background:%s1f">'
			'<svg viewBox="0 0 24 24" fill="none" stroke="%s" stroke-width="1.7" '
			'stroke-linecap="round" stroke-linejoin="round">%s</svg></span>'
			'<span class="tx"><span class="t">%s</span>'
			'<span class="s">%s</span></span></a>'
			% (route, colour, colour, GLYPHS[glyph], label, sub))
	out.append("</div>")
	return "\n".join(out)


def make_block():
	"""Just the record. Attaching it to the workspaces happens after, because a
	workspace must not be saved before the block it references exists."""
	if frappe.db.exists("Custom HTML Block", BLOCK):
		doc = frappe.get_doc("Custom HTML Block", BLOCK)
	else:
		doc = frappe.new_doc("Custom HTML Block")
		doc.name = BLOCK
	doc.html = html()
	doc.style = STYLE
	doc.script = ""
	doc.private = 0
	doc.flags.ignore_permissions = True
	doc.save()


def install():
	make_block()

	for ws in ("RMC Dashboard", "RMC Management", "RMC Production", "RMC Materials",
	           "RMC Dispatch", "RMC Quality", "RMC Setup"):
		if not frappe.db.exists("Workspace", ws):
			continue
		w = frappe.get_doc("Workspace", ws)
		if not any(r.custom_block_name == BLOCK for r in w.custom_blocks):
			w.append("custom_blocks", {"custom_block_name": BLOCK, "label": BLOCK})
		blocks = [b for b in json.loads(w.content or "[]") if b.get("type") != "custom_block"]
		# after the header + intro, before the cards
		at = min(2, len(blocks))
		blocks.insert(at, {"id": "rmcnav000", "type": "custom_block",
		                   "data": {"custom_block_name": BLOCK, "col": 12}})
		w.content = json.dumps(blocks)
		w.flags.ignore_permissions = True
		w.save()

	frappe.db.commit()
	frappe.clear_cache()
	print("  + navigator block on the RMC workspaces")


run = install

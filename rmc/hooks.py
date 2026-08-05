app_name = "rmc"
app_title = "RMC Plant Management"
app_publisher = "Midhuna Tech"
app_description = "Ready Mix Concrete plant ERP for Frappe/ERPNext v16"
app_email = "aimidhunatech@gmail.com"
app_license = "mit"

required_apps = ["erpnext"]

# Purpose-drawn icon set, so every doctype, workspace and shortcut reads as an
# RMC plant rather than sharing one generic glyph.
app_include_icons = ["/assets/rmc/icons/rmc-icons.svg"]

# Shared desk helpers — the Period picker every board and report uses.
# The file must exist before this hook is added: a missing bundle 404s and
# takes the rest of the desk bundle down with it.
app_include_js = ["rmc.bundle.js"]

app_home = "/app/rmc-dashboard"

add_to_apps_screen = [
	{
		"name": app_name,
		"logo": "/assets/rmc/images/rmc-logo.svg",
		"title": app_title,
		"route": app_home,
		"has_permission": "rmc.check_app_permission",
	}
]

# The challan's QR must be embedded in the HTML: the PDF renderer cannot fetch
# an authenticated endpoint, so a <img src="/api/..."> prints as a broken image.
jinja = {
	"methods": ["rmc.utils.qr_data_uri"],
}

after_install = "rmc.setup.after_install"
after_migrate = "rmc.setup.after_migrate"

# ERPNext core doctypes are extended through events + custom fields only, never
# forked, so the app survives an ERPNext upgrade.
doc_events = {
	"Sales Invoice": {
		"on_cancel": "rmc.events.on_sales_invoice_cancel",
	},
}

scheduler_events = {
	# the PLC feed: a reading of every tag, around the clock
	"cron": {
		"*/15 * * * *": ["rmc.plc.poll"],
	},
	"daily": [
		"rmc.tasks.refresh_order_status",
		"rmc.tasks.flag_due_maintenance",
		"rmc.plc.purge",
	],
}

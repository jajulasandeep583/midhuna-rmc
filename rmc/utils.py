"""Helpers exposed to print formats through the jinja hook."""

import base64
import io

import frappe


def qr_data_uri(data, box_size=4, border=2):
	"""Return a QR code as an inline data URI.

	Print formats are rendered to PDF by a headless browser that cannot reach
	authenticated endpoints, so the image has to be embedded in the HTML rather
	than fetched.
	"""
	if not data:
		return ""
	try:
		import qrcode

		img = qrcode.make(str(data), box_size=box_size, border=border)
		buf = io.BytesIO()
		img.save(buf, format="PNG")
		return "data:image/png;base64,%s" % base64.b64encode(buf.getvalue()).decode()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "RMC: QR generation failed")
		return ""

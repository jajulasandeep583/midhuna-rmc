"""Branded print formats — the Delivery Challan that travels with every load.

A4, Midhunatech-branded, with the QR the site uses to verify the load and a
signature block for the receiver. Idempotent.
"""

import frappe

CHALLAN_HTML = """
<div class="rmc-challan">
  <table class="hdr">
    <tr>
      <td class="brandcell">
        <div class="brand">MIDHUNATECH</div>
        <div class="brandsub">RMC PLANT &middot; DCS &amp; PLC ERP INTEGRATION</div>
        <div class="plant">{{ doc.get("plant_name") or frappe.db.get_single_value("RMC Settings", "default_plant") or "" }}</div>
      </td>
      <td class="titlecell">
        <div class="title">DELIVERY CHALLAN</div>
        <table class="meta">
          <tr><td>Challan No</td><td><b>{{ doc.name }}</b></td></tr>
          <tr><td>Date</td><td><b>{{ frappe.utils.formatdate(doc.challan_date, "dd-MM-yyyy") }}</b></td></tr>
          <tr><td>Order</td><td>{{ doc.concrete_order or "" }}</td></tr>
        </table>
      </td>
    </tr>
  </table>

  <table class="party">
    <tr>
      <td>
        <div class="lbl">Customer</div>
        <div class="val">{{ doc.customer }}</div>
        <div class="lbl">Site Address</div>
        <div class="val small">{{ frappe.db.get_value("Construction Site", doc.construction_site, "site_address") or "" }}</div>
      </td>
      <td>
        <div class="lbl">Concrete Grade</div>
        <div class="val big">{{ doc.grade }}</div>
        <div class="lbl">Quantity</div>
        <div class="val big">{{ "%.2f"|format(doc.qty_m3) }} m&sup3;</div>
      </td>
    </tr>
  </table>

  <table class="detail">
    <thead>
      <tr><th style="width:8%">S.No</th><th style="width:42%">Particulars</th><th>Details</th></tr>
    </thead>
    <tbody>
      <tr><td>1</td><td>Quantity</td><td>{{ "%.2f"|format(doc.qty_m3) }} m&sup3;</td></tr>
      <tr><td>2</td><td>Concrete Grade</td><td>{{ doc.grade }}</td></tr>
      <tr><td>3</td><td>Vehicle No</td><td>{{ doc.transit_mixer }}</td></tr>
      <tr><td>4</td><td>Driver Name</td><td>{{ doc.driver_name or "" }}</td></tr>
      <tr><td>5</td><td>Dispatch Time</td><td>{{ frappe.utils.format_datetime(doc.dispatch_time, "dd-MM-yyyy HH:mm") if doc.dispatch_time else "" }}</td></tr>
      <tr><td>6</td><td>Site Arrival Time</td><td>{{ frappe.utils.format_datetime(doc.site_arrival_time, "dd-MM-yyyy HH:mm") if doc.site_arrival_time else "" }}</td></tr>
      <tr><td>7</td><td>Slump at Site</td><td>{{ doc.slump_mm or "-" }} mm</td></tr>
      <tr><td>8</td><td>Batch Reference</td><td>{{ doc.batch_production or "-" }}</td></tr>
    </tbody>
  </table>

  <table class="foot">
    <tr>
      <td class="qrcell">
        {% set qr = qr_data_uri(doc.qr_code or doc.name) %}
        {% if qr %}<img class="qr" src="{{ qr }}" />{% endif %}
        <div class="qrtext">Scan to verify<br/>{{ doc.qr_code or doc.name }}</div>
      </td>
      <td class="notecell">
        <div class="note"><b>Note:</b> Concrete must be placed within 90 minutes of dispatch.
        Any water added at site is at the customer's risk and voids the strength guarantee.
        Please verify quantity and grade before unloading.</div>
        <div class="amt">Rate: &#8377; {{ "%.2f"|format(doc.rate or 0) }} / m&sup3; &nbsp;&nbsp;
          Amount: <b>&#8377; {{ "%.2f"|format(doc.amount or 0) }}</b></div>
      </td>
      <td class="signcell">
        <div class="sigbox">
          {% if doc.customer_signature %}<img class="sig" src="{{ doc.customer_signature }}" />{% endif %}
        </div>
        <div class="siglbl">Customer Signature</div>
        <div class="signame">{{ doc.received_by or "" }}</div>
      </td>
    </tr>
  </table>

  <div class="tagline">MIDHUNATECH &middot; Monitor &middot; Manage &middot; Optimize &middot; Grow
    &nbsp;|&nbsp; aimidhunatech@gmail.com</div>
</div>

<style>
  .rmc-challan { font-family: "Segoe UI", Arial, sans-serif; color:#14212b; font-size:11pt; }
  .rmc-challan table { width:100%; border-collapse:collapse; }
  .hdr td { vertical-align:top; padding-bottom:8px; border-bottom:3px solid #0b3d91; }
  .brand { font-size:22pt; font-weight:800; color:#0b3d91; letter-spacing:.5px; }
  .brandsub { font-size:8pt; letter-spacing:1.5px; color:#c8102e; font-weight:700; }
  .plant { font-size:9pt; color:#4a5b68; margin-top:4px; }
  .titlecell { text-align:right; width:42%; }
  .title { font-size:16pt; font-weight:800; color:#0b3d91; letter-spacing:1px; }
  .meta { width:auto; margin-left:auto; font-size:9.5pt; }
  .meta td { padding:1px 4px; text-align:right; }
  .meta td:first-child { color:#5c6b78; }
  .party { margin-top:10px; border:1px solid #cbd5dd; }
  .party td { width:50%; padding:8px 10px; vertical-align:top; border-right:1px solid #cbd5dd; }
  .party td:last-child { border-right:none; }
  .lbl { font-size:8pt; text-transform:uppercase; letter-spacing:.8px; color:#7c8b98; margin-top:4px; }
  .val { font-size:11pt; font-weight:600; }
  .val.big { font-size:14pt; font-weight:800; color:#0b3d91; }
  .val.small { font-size:9.5pt; font-weight:400; }
  .detail { margin-top:10px; }
  .detail th { background:#0b3d91; color:#fff; font-size:9.5pt; padding:6px 8px; text-align:left; }
  .detail td { border:1px solid #cbd5dd; padding:5px 8px; font-size:10pt; }
  .foot { margin-top:12px; }
  .foot td { vertical-align:top; padding:6px; border:1px solid #cbd5dd; }
  .qrcell { width:22%; text-align:center; }
  .qr { width:100px; height:100px; }
  .qrtext { font-size:7.5pt; color:#5c6b78; margin-top:3px; }
  .notecell { width:48%; }
  .note { font-size:8.5pt; color:#3d4d59; line-height:1.35; }
  .amt { margin-top:10px; font-size:10.5pt; }
  .signcell { width:30%; text-align:center; }
  .sigbox { height:70px; border-bottom:1px solid #8a99a6; }
  .sig { max-height:66px; max-width:100%; }
  .siglbl { font-size:8.5pt; color:#5c6b78; margin-top:3px; }
  .signame { font-size:9.5pt; font-weight:600; }
  .tagline { margin-top:10px; text-align:center; font-size:8pt; letter-spacing:1px;
             color:#0b3d91; border-top:1px solid #cbd5dd; padding-top:6px; }
</style>
"""


def install():
	_upsert("RMC Delivery Challan", "Delivery Challan", CHALLAN_HTML)
	frappe.db.commit()
	print("  + print format: RMC Delivery Challan")


def _upsert(name, doctype, html):
	fields = {
		"doc_type": doctype, "module": "RMC Dispatch", "print_format_type": "Jinja",
		"html": html, "standard": "No", "custom_format": 1, "disabled": 0,
		"font_size": 11, "margin_top": 10, "margin_bottom": 10,
		"margin_left": 10, "margin_right": 10, "default_print_language": "en",
	}
	if frappe.db.exists("Print Format", name):
		doc = frappe.get_doc("Print Format", name)
		doc.update(fields)
		doc.save(ignore_permissions=True)
	else:
		frappe.get_doc({"doctype": "Print Format", "name": name, **fields}).insert(
			ignore_permissions=True)
	# make it the default for the doctype
	if not frappe.db.exists("Property Setter", {"doc_type": doctype, "property": "default_print_format"}):
		frappe.get_doc({
			"doctype": "Property Setter", "doctype_or_field": "DocType", "doc_type": doctype,
			"property": "default_print_format", "value": name, "property_type": "Data",
		}).insert(ignore_permissions=True)

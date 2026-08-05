frappe.pages['rmc-order-360'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper, title: 'Order 360', single_column: true,
	});
	new Order360(page);
};

class Order360 {
	constructor(page) {
		this.page = page;
		this.$body = $(page.body);
		this.$body.html(`<div class="rmcp">
			<div class="hero" id="o3-hero"><h2>Loading…</h2>
				<div class="sub">Pick an order above, or choose one from the list below</div></div>
			<div class="grid">
				<div class="card" style="grid-column:span 2"><h4>Loads delivered</h4>
					<div id="o3-challans"></div></div>
				<div class="card"><h4>Batches</h4><div id="o3-batches"></div></div>
			</div>
			<div class="grid" style="margin-top:14px">
				<div class="card"><h4>Cube tests</h4><div id="o3-cubes"></div></div>
				<div class="card"><h4>Site</h4><div id="o3-site"></div></div>
				<div class="card"><h4>Other open orders</h4><div id="o3-recent"></div></div>
			</div></div>` + `
<style>
	.rmcp{max-width:1200px;margin:0 auto}
	.rmcp .hero{background:linear-gradient(120deg,#0b2f5c,#12508f);color:#fff;
		border-radius:14px;padding:18px 22px;margin-bottom:16px}
	.rmcp .hero h2{margin:0;font-size:20px;font-weight:800}
	.rmcp .hero .sub{opacity:.82;font-size:13px;margin-top:2px}
	.rmcp .strip{display:flex;gap:24px;flex-wrap:wrap;margin-top:14px}
	.rmcp .stat .n{font-size:25px;font-weight:800;line-height:1.15}
	.rmcp .stat .l{font-size:11px;opacity:.85;text-transform:uppercase;letter-spacing:.6px}
	.rmcp .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
	.rmcp .card{background:var(--card-bg,#fff);border:1px solid var(--border-color,#e2e6ea);
		border-radius:12px;padding:15px 17px}
	.rmcp .card h4{margin:0 0 11px;font-size:12px;text-transform:uppercase;
		letter-spacing:.7px;color:var(--text-muted,#6c7680)}
	.rmcp table{width:100%;font-size:13px;border-collapse:collapse}
	.rmcp th{text-align:left;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;
		color:var(--text-muted,#6c7680);padding:4px 6px;
		border-bottom:1px solid var(--border-color,#e2e6ea)}
	.rmcp td{padding:5px 6px;border-bottom:1px solid var(--border-color,#f0f2f4)}
	.rmcp .num{text-align:right;font-variant-numeric:tabular-nums}
	.rmcp .pill{display:inline-block;padding:2px 10px;border-radius:11px;
		font-size:11px;font-weight:800}
	.rmcp .ok{background:#e7f7ec;color:#12793d}
	.rmcp .warn{background:#fff5e0;color:#9a6a00}
	.rmcp .bad{background:#fdeaea;color:#b3261e}
	.rmcp .mute{background:#eef0f2;color:#5c6670}
	.rmcp .bar{height:8px;border-radius:5px;background:var(--bg-light-gray,#eef0f2);overflow:hidden}
	.rmcp .bar span{display:block;height:100%;background:#1a7f4b}
	.rmcp .bar.low span{background:#d93a2b}
	.rmcp .empty{color:var(--text-muted,#6c7680);font-size:13px;padding:8px 0}
</style>
`);

		this.field = this.page.add_field({
			fieldtype: 'Link', fieldname: 'order', label: __('Concrete Order'),
			options: 'Concrete Order',
			get_query: () => ({ filters: { docstatus: 1 } }),
			change: () => this.refresh(),
		});
		this.page.set_primary_action(__('Refresh'), () => this.refresh(), 'refresh');

		this.load_recent();

		// never land on an empty page: take the order from the route, else the
		// most recently required one still open, else simply the latest order
		const route = frappe.get_route();
		if (route[1]) {
			this.field.set_value(route[1]);
		} else {
			this.pick_default();
		}
	}

	pick_default() {
		frappe.db.get_list('Concrete Order', {
			filters: { docstatus: 1, status: ['in', ['Open', 'In Progress']] },
			fields: ['name'], order_by: 'required_from desc', limit: 1,
		}).then((rows) => {
			if (rows && rows.length) return this.field.set_value(rows[0].name);
			return frappe.db.get_list('Concrete Order', {
				filters: { docstatus: 1 }, fields: ['name'],
				order_by: 'creation desc', limit: 1,
			}).then((r2) => {
				if (r2 && r2.length) this.field.set_value(r2[0].name);
				else $('#o3-hero').html('<h2>No orders yet</h2><div class="sub">' +
					'Create a Concrete Order and it will appear here.</div>');
			});
		});
	}

	load_recent() {
		frappe.db.get_list('Concrete Order', {
			filters: { docstatus: 1, status: ['in', ['Open', 'In Progress']] },
			fields: ['name', 'customer', 'grade', 'order_qty_m3', 'pending_qty_m3',
				'required_from'],
			order_by: 'required_from asc', limit: 12,
		}).then((rows) => {
			if (!rows || !rows.length) {
				$('#o3-recent').html('<div class="empty">No open orders.</div>');
				return;
			}
			const html = rows.map((o) => `<tr>
				<td><a href="#" data-order="${o.name}">${o.name}</a></td>
				<td>${frappe.utils.escape_html((o.customer || '').substring(0, 22))}</td>
				<td>${o.grade || ''}</td>
				<td class="num">${o.pending_qty_m3}</td></tr>`).join('');
			$('#o3-recent').html(`<table><thead><tr><th>Order</th><th>Customer</th>
				<th>Grade</th><th class="num">Pending</th></tr></thead>
				<tbody>${html}</tbody></table>`);
			$('#o3-recent').find('a[data-order]').on('click', (e) => {
				e.preventDefault();
				this.field.set_value($(e.currentTarget).data('order'));
			});
		});
	}

	refresh() {
		const order = this.field.get_value();
		if (!order) return;
		frappe.call({ method: 'rmc.dashboard.order_360', args: { order } })
			.then((r) => this.draw(r.message || {}))
			.catch(() => $('#o3-hero').html('<h2>Could not load that order</h2>'));
	}

	draw(d) {
		const o = d.order || {};
		$('#o3-hero').html(`
			<h2>${o.name || ''} — ${frappe.utils.escape_html(o.customer || '')}</h2>
			<div class="sub">${frappe.utils.escape_html((d.site && d.site.site_name) || '')} ·
				grade ${o.grade || ''} · ${o.status || ''} ·
				required ${o.required_from ? frappe.datetime.str_to_user(o.required_from) : '—'}</div>
			<div class="strip">
				<div class="stat"><div class="n">${o.order_qty_m3 || 0}</div><div class="l">Ordered m³</div></div>
				<div class="stat"><div class="n">${o.delivered_qty_m3 || 0}</div><div class="l">Delivered m³</div></div>
				<div class="stat"><div class="n">${o.pending_qty_m3 || 0}</div><div class="l">Pending m³</div></div>
				<div class="stat"><div class="n">${d.progress_pct || 0}%</div><div class="l">Complete</div></div>
				<div class="stat"><div class="n">${format_currency(o.order_value || 0)}</div><div class="l">Order value</div></div>
				<div class="stat"><div class="n">${format_currency(d.invoiced_value || 0)}</div><div class="l">Invoiced</div></div>
			</div>`);

		$('#o3-challans').html((d.challans || []).length ? `<table>
			<thead><tr><th>Challan</th><th>Date</th><th class="num">m³</th><th>Vehicle</th>
			<th>Driver</th><th class="num">Cycle</th><th class="num">Slump</th>
			<th>Status</th><th>Invoice</th></tr></thead>
			<tbody>${d.challans.map((c) => `<tr>
				<td><a href="/app/delivery-challan/${encodeURIComponent(c.name)}">${c.name}</a></td>
				<td>${frappe.datetime.str_to_user(c.challan_date)}</td>
				<td class="num">${c.qty_m3}</td><td>${c.transit_mixer || ''}</td>
				<td>${frappe.utils.escape_html(c.driver_name || '')}</td>
				<td class="num">${c.cycle_time_min || '—'}</td>
				<td class="num">${c.slump_mm || '—'}</td>
				<td><span class="pill ${c.status === 'Returned' ? 'ok' : 'warn'}">${c.status}</span></td>
				<td>${c.sales_invoice ? `<a href="/app/sales-invoice/${encodeURIComponent(c.sales_invoice)}">bill</a>` : '—'}</td>
			</tr>`).join('')}</tbody></table>`
			: '<div class="empty">No loads delivered against this order yet.</div>');

		$('#o3-batches').html((d.batches || []).length ? `<table>
			<thead><tr><th>Batch</th><th>Date</th><th class="num">m³</th>
			<th class="num">Cost/m³</th></tr></thead>
			<tbody>${d.batches.map((b) => `<tr>
				<td><a href="/app/batch-production/${encodeURIComponent(b.name)}">${b.name}</a></td>
				<td>${frappe.datetime.str_to_user(b.production_date)}</td>
				<td class="num">${b.qty_m3}</td>
				<td class="num">${format_currency(b.cost_per_m3 || 0)}</td></tr>`).join('')}
			</tbody></table>` : '<div class="empty">No batches yet.</div>');

		$('#o3-cubes').html((d.cubes || []).length ? `<table>
			<thead><tr><th>Test</th><th>Age</th><th class="num">Got</th>
			<th class="num">Needed</th><th>Result</th></tr></thead>
			<tbody>${d.cubes.map((c) => `<tr>
				<td><a href="/app/cube-test/${encodeURIComponent(c.name)}">${c.name}</a></td>
				<td>${c.age_days}d</td><td class="num">${c.avg_strength_mpa}</td>
				<td class="num">${Number(c.required_strength_mpa).toFixed(1)}</td>
				<td><span class="pill ${c.result === 'Pass' ? 'ok' : 'bad'}">${c.result}</span></td>
			</tr>`).join('')}</tbody></table>`
			: '<div class="empty">No cube tests sampled from this order.</div>');

		const s = d.site || {};
		$('#o3-site').html(`<table><tbody>
			<tr><td>Site</td><td>${frappe.utils.escape_html(s.site_name || '')}</td></tr>
			<tr><td>Address</td><td>${frappe.utils.escape_html(s.site_address || '')}</td></tr>
			<tr><td>Distance</td><td>${s.distance_km || 0} km</td></tr>
			<tr><td>Contact</td><td>${frappe.utils.escape_html(s.contact_person || '')}
				${s.contact_no || ''}</td></tr>
			<tr><td>Open the order</td>
				<td><a href="/app/concrete-order/${encodeURIComponent(o.name || '')}">${o.name || ''}</a></td></tr>
			</tbody></table>`);
	}
}

frappe.pages['rmc-live-dashboard'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper, title: 'RMC Live Dashboard', single_column: true,
	});
	new RMCLiveDashboard(page);
};

class RMCLiveDashboard {
	constructor(page) {
		this.page = page;
		this.$body = $(page.body);
		this.render_shell();
		this.refresh();
		this.page.set_primary_action(__('Refresh'), () => this.refresh(), 'refresh');
		// the plant floor leaves this on a wall screen — keep it current
		this.timer = setInterval(() => this.refresh(), 120000);
		$(wrapper).on('remove', () => clearInterval(this.timer));
	}

	render_shell() {
		this.$body.html(`
		<style>
			.rmcd{max-width:1180px;margin:0 auto}
			.rmcd .hero{background:linear-gradient(120deg,#0b2f5c,#12508f);color:#fff;
				border-radius:14px;padding:20px 24px;margin-bottom:18px}
			.rmcd .hero h2{margin:0;font-size:22px;font-weight:800}
			.rmcd .hero .loc{opacity:.8;font-size:13px;margin-top:2px}
			.rmcd .strip{display:flex;gap:26px;flex-wrap:wrap;margin-top:16px}
			.rmcd .stat .n{font-size:28px;font-weight:800;line-height:1.1}
			.rmcd .stat .l{font-size:11px;opacity:.85;text-transform:uppercase;letter-spacing:.6px}
			.rmcd .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}
			.rmcd .card{background:var(--card-bg,#fff);border:1px solid var(--border-color,#e2e6ea);
				border-radius:12px;padding:16px 18px}
			.rmcd .card h4{margin:0 0 12px;font-size:13px;text-transform:uppercase;
				letter-spacing:.7px;color:var(--text-muted,#6c7680)}
			.rmcd .pill{display:inline-block;padding:3px 12px;border-radius:12px;
				font-size:12px;font-weight:800}
			.rmcd .pill.Running{background:#e7f7ec;color:#12793d}
			.rmcd .pill.Idle{background:#fff5e0;color:#9a6a00}
			.rmcd .pill.Breakdown{background:#fdeaea;color:#b3261e}
			.rmcd .pill.Stopped{background:#eef0f2;color:#5c6670}
			.rmcd table{width:100%;font-size:13px;border-collapse:collapse}
			.rmcd th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.5px;
				color:var(--text-muted,#6c7680);padding:4px 6px;border-bottom:1px solid var(--border-color,#e2e6ea)}
			.rmcd td{padding:5px 6px;border-bottom:1px solid var(--border-color,#f0f2f4)}
			.rmcd .bar{height:8px;border-radius:5px;background:var(--bg-light-gray,#eef0f2);overflow:hidden}
			.rmcd .bar span{display:block;height:100%;background:#1a7f4b}
			.rmcd .bar.low span{background:#d93a2b}
			.rmcd .low-txt{color:#b3261e;font-weight:700}
			.rmcd .num{text-align:right;font-variant-numeric:tabular-nums}
		</style>
		<div class="rmcd">
			<div class="hero" id="rmcd-hero"><h2>Loading…</h2></div>
			<div class="grid">
				<div class="card" style="grid-column:span 2"><h4>Silo &amp; Yard Levels</h4><div id="rmcd-silos"></div></div>
				<div class="card"><h4>Fleet</h4><div id="rmcd-fleet"></div></div>
			</div>
			<div class="grid" style="margin-top:14px">
				<div class="card" style="grid-column:span 3"><h4>Order Book — pending deliveries</h4><div id="rmcd-orders"></div></div>
			</div>
		</div>`);
	}

	refresh() {
		frappe.call({ method: 'rmc.api.plant_status' }).then(r => this.draw_hero(r.message || {}));
		frappe.call({ method: 'rmc.api.silo_levels' }).then(r => this.draw_silos(r.message || []));
		frappe.call({ method: 'rmc.api.order_book' }).then(r => this.draw_orders(r.message || []));
	}

	draw_hero(d) {
		const fmt = (n) => frappe.format(n || 0, { fieldtype: 'Float', precision: 2 });
		$('#rmcd-hero').html(`
			<h2>${frappe.utils.escape_html(d.plant || 'RMC Plant')}
				<span class="pill ${d.status}">${frappe.utils.escape_html(d.status || '')}</span></h2>
			<div class="loc">Power: ${d.power_source || '—'}
				${d.eb_voltage ? '· EB ' + d.eb_voltage + ' V' : ''}
				${d.dg_load_pct ? '· DG ' + d.dg_load_pct + '%' : ''}</div>
			<div class="strip">
				<div class="stat"><div class="n">${fmt(d.today_production_m3)}</div><div class="l">Produced today (m³)</div></div>
				<div class="stat"><div class="n">${fmt(d.today_dispatch_m3)}</div><div class="l">Dispatched (m³)</div></div>
				<div class="stat"><div class="n">${d.today_trips || 0}</div><div class="l">Trips</div></div>
				<div class="stat"><div class="n">${d.availability_pct || 0}%</div><div class="l">Availability</div></div>
				<div class="stat"><div class="n">${fmt(d.running_hours)}h</div><div class="l">Running</div></div>
				<div class="stat"><div class="n">${fmt(d.breakdown_hours)}h</div><div class="l">Breakdown</div></div>
				<div class="stat"><div class="n">${format_currency(d.today_dispatch_value || 0)}</div><div class="l">Dispatch value</div></div>
			</div>`);
	}

	draw_silos(rows) {
		const html = rows.map(s => `
			<tr>
				<td>${frappe.utils.escape_html(s.silo)}</td>
				<td class="num ${s.low ? 'low-txt' : ''}">${s.stock_mt}</td>
				<td class="num">${s.capacity_mt}</td>
				<td style="width:34%">
					<div class="bar ${s.low ? 'low' : ''}"><span style="width:${Math.min(100, s.filled_pct)}%"></span></div>
				</td>
				<td class="num">${s.filled_pct}%</td>
			</tr>`).join('');
		$('#rmcd-silos').html(`<table>
			<thead><tr><th>Silo / Yard</th><th class="num">Stock</th><th class="num">Cap.</th><th>Level</th><th class="num">%</th></tr></thead>
			<tbody>${html}</tbody></table>`);
	}

	draw_orders(rows) {
		if (!rows.length) { $('#rmcd-orders').html('<p class="text-muted">No pending orders.</p>'); return; }
		const html = rows.slice(0, 12).map(o => `
			<tr>
				<td><a href="/app/concrete-order/${encodeURIComponent(o.name)}">${o.name}</a></td>
				<td>${frappe.utils.escape_html(o.customer || '')}</td>
				<td>${frappe.utils.escape_html(o.site_name || '')}</td>
				<td>${o.grade}</td>
				<td class="num">${o.order_qty_m3}</td>
				<td class="num">${o.delivered_qty_m3}</td>
				<td class="num"><b>${o.pending_qty_m3}</b></td>
				<td>${frappe.datetime.str_to_user(o.required_from)}</td>
			</tr>`).join('');
		$('#rmcd-orders').html(`<table>
			<thead><tr><th>Order</th><th>Customer</th><th>Site</th><th>Grade</th>
			<th class="num">Ordered</th><th class="num">Delivered</th><th class="num">Pending</th><th>Required</th></tr></thead>
			<tbody>${html}</tbody></table>`);
	}

	draw_fleet() {}
}

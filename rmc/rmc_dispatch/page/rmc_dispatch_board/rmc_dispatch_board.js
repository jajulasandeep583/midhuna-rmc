frappe.pages['rmc-dispatch-board'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper, title: 'Dispatch Board', single_column: true,
	});
	new DispatchBoard(page);
};

class DispatchBoard {
	constructor(page) {
		this.page = page;
		this.$body = $(page.body);
		this.$body.html(`<div class="rmcp">
			<div class="hero" id="db-hero"><h2>Loading…</h2></div>
			<div class="grid">
				<div class="card" style="grid-column:span 2"><h4>Trips</h4><div id="db-trips"></div></div>
				<div class="card"><h4>Fleet</h4><div id="db-fleet"></div>
					<h4 style="margin-top:16px">Dispatched by day</h4><div id="db-days"></div></div>
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

		this.range = rmc.add_period_fields(this.page, () => this.refresh(), "Last 7 Days");
		this.from_f = this.range.from;
		this.to_f = this.range.to;
		this.cust_f = this.page.add_field({
			fieldtype: 'Link', fieldname: 'customer', label: __('Customer'),
			options: 'Customer', change: () => this.refresh(),
		});
		this.grade_f = this.page.add_field({
			fieldtype: 'Link', fieldname: 'grade', label: __('Grade'),
			options: 'Concrete Grade', change: () => this.refresh(),
		});
		this.mixer_f = this.page.add_field({
			fieldtype: 'Link', fieldname: 'transit_mixer', label: __('Transit Mixer'),
			options: 'Transit Mixer', change: () => this.refresh(),
		});
		this.status_f = this.page.add_field({
			fieldtype: 'Select', fieldname: 'status', label: __('Status'),
			options: ['', 'Dispatched', 'Delivered', 'Returned', 'Cancelled'],
			change: () => this.refresh(),
		});
		this.page.set_primary_action(__('New Challan'), () =>
			frappe.new_doc('Delivery Challan', { challan_date: this.to_f.get_value() }));
		this.page.add_menu_item(__('Today'), () => {
			this.from_f.set_value(frappe.datetime.get_today());
			this.to_f.set_value(frappe.datetime.get_today());
		});
		this.page.add_menu_item(__('Last 7 days'), () => {
			this.from_f.set_value(frappe.datetime.add_days(frappe.datetime.get_today(), -6));
			this.to_f.set_value(frappe.datetime.get_today());
		});
		this.page.add_menu_item(__('This month'), () => {
			this.from_f.set_value(frappe.datetime.month_start());
			this.to_f.set_value(frappe.datetime.get_today());
		});
		this.page.add_menu_item(__('Last 30 days'), () => {
			this.from_f.set_value(frappe.datetime.add_days(frappe.datetime.get_today(), -29));
			this.to_f.set_value(frappe.datetime.get_today());
		});
		this.refresh();
	}

	refresh() {
		frappe.call({
			method: 'rmc.dashboard.dispatch_board',
			args: {
				from_date: this.from_f.get_value(), to_date: this.to_f.get_value(),
				customer: this.cust_f.get_value() || null,
				grade: this.grade_f.get_value() || null,
				transit_mixer: this.mixer_f.get_value() || null,
				status: this.status_f.get_value() || null,
			},
		}).then((r) => this.draw(r.message || {}));
	}

	empty(msg) {
		return `<div class="empty">${msg}
			<a href="#" class="widen" style="margin-left:6px">Show last 30 days</a></div>`;
	}

	bind_widen() {
		this.$body.find('a.widen').off('click').on('click', (e) => {
			e.preventDefault();
			this.range.period.set_value('Last 30 Days');
		});
	}

	draw(d) {
		$('#db-hero').html(`
			<h2>Dispatch — ${frappe.datetime.str_to_user(d.from_date)} to ${frappe.datetime.str_to_user(d.to_date)}</h2>
			<div class="strip">
				<div class="stat"><div class="n">${(d.trips || []).length}</div><div class="l">Trips</div></div>
				<div class="stat"><div class="n">${d.total_qty || 0}</div><div class="l">Dispatched m³</div></div>
				<div class="stat"><div class="n">${format_currency(d.total_value || 0)}</div><div class="l">Value</div></div>
				<div class="stat"><div class="n">${d.avg_cycle || 0}</div><div class="l">Avg cycle min</div></div>
				<div class="stat"><div class="n">${d.available || 0}/${(d.fleet || []).length}</div><div class="l">Mixers free</div></div>
			</div>`);

		const cls = (s) => (s === 'Returned' ? 'ok' : (s === 'Cancelled' ? 'bad' : 'warn'));
		const rows = (d.trips || []).map((t) => `<tr>
			<td><a href="/app/delivery-challan/${encodeURIComponent(t.name)}">${t.name}</a></td>
			<td>${frappe.datetime.str_to_user(t.challan_date)}</td>
			<td>${frappe.utils.escape_html((t.customer || '').substring(0, 24))}</td>
			<td>${frappe.utils.escape_html((t.site_name || '').substring(0, 22))}</td>
			<td>${t.grade || ''}</td><td class="num">${t.qty_m3}</td>
			<td>${t.transit_mixer || ''}</td>
			<td class="num">${t.cycle_time_min || '—'}</td>
			<td class="num">${t.slump_mm || '—'}</td>
			<td><span class="pill ${cls(t.status)}">${t.status}</span></td>
			<td>${t.sales_invoice ? `<a href="/app/sales-invoice/${encodeURIComponent(t.sales_invoice)}">bill</a>` : '—'}</td>
			</tr>`).join('');
		$('#db-trips').html(rows ? `<table><thead><tr><th>Challan</th><th>Date</th><th>Customer</th>
			<th>Site</th><th>Grade</th><th class="num">m³</th><th>Vehicle</th>
			<th class="num">Cycle</th><th class="num">Slump</th><th>Status</th><th>Invoice</th>
			</tr></thead><tbody>${rows}</tbody></table>`
			: this.empty('No loads went out between these dates.'));

		const fcls = { 'Available': 'ok', 'On Trip': 'warn', 'Under Maintenance': 'bad' };
		$('#db-fleet').html(`<table><tbody>${(d.fleet || []).map((f) => `<tr>
			<td>${f.name}</td><td class="num">${f.capacity_m3} m³</td>
			<td><span class="pill ${fcls[f.status] || 'mute'}">${f.status}</span></td>
			</tr>`).join('')}</tbody></table>`);

		const days = d.days || [];
		const max = Math.max(1, ...days.map((x) => x.qty));
		$('#db-days').html(days.length
			? `<div class="spark">${days.map((x) =>
				`<i class="d" title="${x.date}: ${x.qty} m³" style="height:${Math.round(100 * x.qty / max)}%"></i>`).join('')}</div>`
			: '<div class="empty">—</div>');
		this.bind_widen();
	}
}

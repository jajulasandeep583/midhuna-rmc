frappe.pages['rmc-manage'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper, title: 'Management', single_column: true,
	});
	new Management(page);
};

class Management {
	constructor(page) {
		this.page = page;
		this.$body = $(page.body);
		this.$body.html(`<div class="rmcp">
			<div class="hero" id="mg-hero"><h2>Loading…</h2></div>
			<div id="mg-note"></div>
			<div class="kpis" id="mg-kpis"></div>
			<div class="grid">
				<div class="card" style="grid-column:span 2"><h4>Produced vs dispatched</h4>
					<div id="mg-trend"></div></div>
				<div class="card"><h4>Sales by grade</h4><div id="mg-grades"></div></div>
			</div>
			<div class="grid" style="margin-top:14px">
				<div class="card"><h4>Top customers</h4><div id="mg-cust"></div></div>
				<div class="card"><h4>Material purchased</h4><div id="mg-mat"></div></div>
				<div class="card"><h4>Outstanding receivables</h4><div id="mg-recv"></div></div>
			</div>
			<div class="grid" style="margin-top:14px">
				<div class="card"><h4>Stock on hand</h4><div id="mg-stock"></div></div>
				<div class="card"><h4>Silos needing a refill</h4><div id="mg-low"></div></div>
				<div class="card"><h4>Go to</h4><div id="mg-links"></div></div>
			</div></div>` + `
<style>
	.rmcp{max-width:1240px;margin:0 auto}
	.rmcp .hero{background:linear-gradient(120deg,#0b2f5c,#12508f);color:#fff;
		border-radius:14px;padding:18px 22px;margin-bottom:16px}
	.rmcp .hero h2{margin:0;font-size:20px;font-weight:800}
	.rmcp .hero .sub{opacity:.82;font-size:13px;margin-top:3px}
	.rmcp .strip{display:flex;gap:24px;flex-wrap:wrap;margin-top:14px}
	.rmcp .stat .n{font-size:24px;font-weight:800;line-height:1.15}
	.rmcp .stat .l{font-size:11px;opacity:.85;text-transform:uppercase;letter-spacing:.6px}
	.rmcp .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));
		gap:12px;margin-bottom:14px}
	.rmcp .kpi{background:var(--card-bg,#fff);border:1px solid var(--border-color,#e2e6ea);
		border-radius:12px;padding:14px 16px;border-left:4px solid #94a3b8}
	.rmcp .kpi .n{font-size:21px;font-weight:800;line-height:1.2}
	.rmcp .kpi .l{font-size:11px;text-transform:uppercase;letter-spacing:.6px;
		color:var(--text-muted,#6c7680);margin-top:3px}
	.rmcp .kpi .x{font-size:11.5px;color:var(--text-muted,#6c7680);margin-top:5px}
	.rmcp .kpi.sale{border-left-color:#9333EA}.rmcp .kpi.prod{border-left-color:#16A34A}
	.rmcp .kpi.buy{border-left-color:#B45309}.rmcp .kpi.marg{border-left-color:#0F766E}
	.rmcp .kpi.stock{border-left-color:#7C2D12}.rmcp .kpi.recv{border-left-color:#DC2626}
	.rmcp .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
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
	.rmcp .pill{display:inline-block;padding:2px 10px;border-radius:11px;font-size:11px;font-weight:800}
	.rmcp .ok{background:#e7f7ec;color:#12793d}.rmcp .warn{background:#fff5e0;color:#9a6a00}
	.rmcp .bad{background:#fdeaea;color:#b3261e}.rmcp .mute{background:#eef0f2;color:#5c6670}
	.rmcp .bar{height:8px;border-radius:5px;background:var(--bg-light-gray,#eef0f2);overflow:hidden}
	.rmcp .bar span{display:block;height:100%;background:#1a7f4b}
	.rmcp .bar.low span{background:#d93a2b}
	.rmcp .empty{color:var(--text-muted,#6c7680);font-size:13px;padding:8px 0}
	.rmcp .spark{display:flex;align-items:flex-end;gap:2px;height:54px;margin-top:6px}
	.rmcp .spark i{flex:1;background:#2563EB;border-radius:2px 2px 0 0;min-height:2px;opacity:.85}
	.rmcp .spark i.d{background:#9333EA}
</style>
`);

		this.range = rmc.add_period_fields(this.page, () => this.refresh(), "This Month");
		this.from_f = this.range.from;
		this.to_f = this.range.to;
		this.plant_f = this.page.add_field({
			fieldtype: 'Link', fieldname: 'plant', label: __('Plant'),
			options: 'RMC Plant', change: () => this.refresh(),
		});
		this.page.set_primary_action(__('Refresh'), () => this.refresh(), 'refresh');
		this.page.add_menu_item(__('This month'), () => {
			this.from_f.set_value(frappe.datetime.month_start());
			this.to_f.set_value(frappe.datetime.get_today());
		});
		this.page.add_menu_item(__('Last 90 days'), () => {
			this.from_f.set_value(frappe.datetime.add_days(frappe.datetime.get_today(), -89));
			this.to_f.set_value(frappe.datetime.get_today());
		});
		this.refresh();
	}

	refresh() {
		frappe.call({
			method: 'rmc.dashboard.management',
			args: {
				from_date: this.from_f.get_value(), to_date: this.to_f.get_value(),
				plant: this.plant_f.get_value() || null,
			},
		}).then((r) => this.draw(r.message || {}));
	}

	draw(d) {
		const s = d.sales || {}, p = d.production || {}, b = d.purchase || {}, m = d.margin || {};
		$('#mg-hero').html(`
			<h2>Management — one view</h2>
			<div class="sub">Sales, production, purchase, stock and receivables ·
				${d.period ? frappe.datetime.str_to_user(d.period.from) + ' to ' +
				frappe.datetime.str_to_user(d.period.to) : ''}</div>
			<div class="strip">
				<div class="stat"><div class="n">${format_currency(s.value || 0)}</div><div class="l">Sales value</div></div>
				<div class="stat"><div class="n">${s.qty || 0}</div><div class="l">Sold m³</div></div>
				<div class="stat"><div class="n">${format_currency(b.value || 0)}</div><div class="l">Material bought</div></div>
				<div class="stat"><div class="n">${m.pct || 0}%</div><div class="l">Gross margin</div></div>
				<div class="stat"><div class="n">${d.open_orders || 0}</div><div class="l">Open orders</div></div>
				<div class="stat"><div class="n">${d.pending_m3 || 0}</div><div class="l">Pending m³</div></div>
			</div>`);

		$('#mg-note').html((s.loads || 0) || (b.trucks || 0) ? '' :
			`<div class="card" style="margin-bottom:12px;border-left:4px solid #B45309">
				Nothing was sold or bought between these dates.
				<a href="#" id="mg-widen">Show the last 30 days</a> instead.</div>`);
		$('#mg-widen').off('click').on('click', (e) => {
			e.preventDefault();
			this.range.period.set_value('Last 30 Days');
		});

		const kpi = (cls, n, l, x) => `<div class="kpi ${cls}"><div class="n">${n}</div>
			<div class="l">${l}</div><div class="x">${x}</div></div>`;
		$('#mg-kpis').html([
			kpi('sale', format_currency(s.value || 0), 'Sales',
				`${s.loads || 0} loads · ${s.customers || 0} customers · avg ${format_currency(s.avg_rate || 0)}/m³`),
			kpi('prod', `${p.qty || 0} m³`, 'Produced',
				`${p.batches || 0} batches · cost ${format_currency(p.cost_per_m3 || 0)}/m³`),
			kpi('buy', format_currency(b.value || 0), 'Purchased',
				`${b.trucks || 0} trucks · ${b.mt || 0} MT · ${b.suppliers || 0} suppliers`),
			kpi('marg', format_currency(m.gross || 0), 'Gross margin',
				`${m.pct || 0}% over material cost`),
			kpi('stock', format_currency(d.stock_value || 0), 'Stock on hand',
				`${(d.stock || []).length} item groups`),
			kpi('recv', format_currency(d.receivable_total || 0), 'Receivables',
				`${(d.receivables || []).length} customers owing`),
		].join(''));

		const daily = d.daily || [];
		const max = Math.max(1, ...daily.map(x => Math.max(x.produced, x.dispatched)));
		$('#mg-trend').html(`
			<div class="spark">${daily.map(x =>
				`<i title="${x.d}: ${x.produced} m³ produced" style="height:${Math.round(100 * x.produced / max)}%"></i>`).join('')}</div>
			<div class="spark">${daily.map(x =>
				`<i class="d" title="${x.d}: ${x.dispatched} m³ dispatched" style="height:${Math.round(100 * x.dispatched / max)}%"></i>`).join('')}</div>
			<div style="font-size:11.5px;opacity:.7;margin-top:6px">
				Blue = produced · Purple = dispatched · ${daily.length} days</div>`);

		const tot = (d.by_grade || []).reduce((a, g) => a + g.qty, 0) || 1;
		$('#mg-grades').html((d.by_grade || []).map(g => `
			<div style="margin-bottom:8px">
				<div style="display:flex;justify-content:space-between;font-size:12.5px">
					<b>${g.grade}</b><span>${g.qty} m³ · ${format_currency(g.value)}</span></div>
				<div class="bar"><span style="width:${Math.round(100 * g.qty / tot)}%"></span></div>
			</div>`).join('') || '<div class="empty">No sales in this period.</div>');

		$('#mg-cust').html((d.top_customers || []).length ? `<table>
			<thead><tr><th>Customer</th><th class="num">m³</th><th class="num">Value</th></tr></thead>
			<tbody>${d.top_customers.map(c => `<tr>
				<td><a href="/app/customer/${encodeURIComponent(c.customer)}">${frappe.utils.escape_html(c.customer.substring(0, 28))}</a></td>
				<td class="num">${c.qty}</td><td class="num">${format_currency(c.value)}</td>
			</tr>`).join('')}</tbody></table>` : '<div class="empty">No sales.</div>');

		$('#mg-mat').html((d.top_materials || []).length ? `<table>
			<thead><tr><th>Item</th><th class="num">MT</th><th class="num">Value</th></tr></thead>
			<tbody>${d.top_materials.map(x => `<tr>
				<td>${x.item_code}</td><td class="num">${Number(x.mt).toFixed(1)}</td>
				<td class="num">${format_currency(x.value)}</td></tr>`).join('')}</tbody></table>`
			: '<div class="empty">No purchases.</div>');

		$('#mg-recv').html((d.receivables || []).length ? `<table>
			<thead><tr><th>Customer</th><th class="num">Billed</th><th class="num">Outstanding</th></tr></thead>
			<tbody>${d.receivables.map(r => `<tr>
				<td>${frappe.utils.escape_html(r.customer.substring(0, 26))}</td>
				<td class="num">${format_currency(r.billed)}</td>
				<td class="num"><b>${format_currency(r.outstanding)}</b></td></tr>`).join('')}</tbody></table>`
			: '<div class="empty">Nothing outstanding.</div>');

		$('#mg-stock').html((d.stock || []).length ? `<table>
			<thead><tr><th>Item group</th><th class="num">Value</th></tr></thead>
			<tbody>${d.stock.map(x => `<tr><td>${x.item_group}</td>
				<td class="num">${format_currency(x.value)}</td></tr>`).join('')}</tbody></table>`
			: '<div class="empty">No stock.</div>');

		$('#mg-low').html((d.low_silos || []).length ? `<table>
			<thead><tr><th>Silo</th><th class="num">Stock</th><th class="num">Days</th></tr></thead>
			<tbody>${d.low_silos.map(x => `<tr><td>${x.silo}</td>
				<td class="num"><span class="pill bad">${x.stock_mt}</span></td>
				<td class="num">${x.days_cover === null ? '—' : x.days_cover}</td></tr>`).join('')}</tbody></table>`
			: '<div class="empty">Every silo is above its alert level.</div>');

		$('#mg-links').html(`
			<a class="btn btn-default btn-sm" href="/app/rmc-control-tower">Control Tower</a>
			<a class="btn btn-default btn-sm" href="/app/rmc-silo-board">Silo &amp; Stock</a>
			<a class="btn btn-default btn-sm" href="/app/rmc-dispatch-board">Dispatch</a>
			<a class="btn btn-default btn-sm" href="/app/rmc-reports">All reports</a>
			<a class="btn btn-default btn-sm" href="/app/query-report/Customer Wise Sales">Customer sales</a>
			<a class="btn btn-default btn-sm" href="/app/accounts-receivable">Receivables</a>`);
	}
}

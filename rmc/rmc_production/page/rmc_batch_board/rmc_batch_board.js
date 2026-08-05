frappe.pages['rmc-batch-board'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper, title: 'Batching Board', single_column: true,
	});
	new BatchBoard(page);
};

class BatchBoard {
	constructor(page) {
		this.page = page;
		this.$body = $(page.body);
		this.$body.html(`<div class="rmcp">
			<div class="hero" id="bb-hero"><h2>Loading…</h2></div>
			<div class="grid">
				<div class="card" style="grid-column:span 2"><h4>Batches</h4><div id="bb-batches"></div></div>
				<div class="card"><h4>Material consumed — actual vs recipe</h4><div id="bb-materials"></div></div>
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
		this.date_field = this.page.add_field({
			fieldtype: 'Date', fieldname: 'date', label: __('Production Date'),
			default: frappe.datetime.get_today(),
			change: () => this.refresh(),
		});
		this.page.set_primary_action(__('New Batch'), () =>
			frappe.new_doc('Batch Production', { production_date: this.date_field.get_value() }));
		this.refresh();
	}

	refresh() {
		frappe.call({ method: 'rmc.dashboard.batch_board',
			args: { date: this.date_field.get_value() } })
			.then((r) => this.draw(r.message || {}));
	}

	draw(d) {
		const shifts = (d.shifts || []).map(s =>
			`<div class="stat"><div class="n">${s.qty.toFixed(2)}</div>
			 <div class="l">${frappe.utils.escape_html(s.shift)} · ${s.loads} loads</div></div>`).join('');
		$('#bb-hero').html(`
			<h2>Batching — ${frappe.datetime.str_to_user(d.date)}</h2>
			<div class="strip">
				<div class="stat"><div class="n">${d.total_qty || 0}</div><div class="l">Total m³</div></div>
				<div class="stat"><div class="n">${(d.batches || []).length}</div><div class="l">Loads</div></div>
				<div class="stat"><div class="n">${format_currency(d.total_cost || 0)}</div><div class="l">Material cost</div></div>
				${shifts}
			</div>`);

		const rows = (d.batches || []).map(b => `<tr>
			<td><a href="/app/batch-production/${encodeURIComponent(b.name)}">${b.name}</a></td>
			<td>${b.shift || ''}</td><td>${b.grade || ''}</td>
			<td class="num">${b.qty_m3}</td>
			<td>${frappe.utils.escape_html(b.customer || '—')}</td>
			<td>${frappe.utils.escape_html(b.operator || '')}</td>
			<td class="num">${format_currency(b.cost_per_m3 || 0)}</td>
			<td>${b.stock_entry ? `<a href="/app/stock-entry/${encodeURIComponent(b.stock_entry)}">SE</a>` : '—'}</td>
			</tr>`).join('');
		$('#bb-batches').html(rows ? `<table><thead><tr><th>Batch</th><th>Shift</th><th>Grade</th>
			<th class="num">m³</th><th>Customer</th><th>Operator</th><th class="num">Cost/m³</th><th>Stock</th>
			</tr></thead><tbody>${rows}</tbody></table>`
			: '<div class="empty">Nothing batched on this date.</div>');

		const mrows = (d.materials || []).map(m => {
			const cls = Math.abs(m.variance_pct) > 2 ? 'bad' : 'ok';
			return `<tr><td>${m.item_code}</td>
				<td class="num">${Number(m.target).toFixed(1)}</td>
				<td class="num">${Number(m.actual).toFixed(1)}</td>
				<td class="num"><span class="pill ${cls}">${m.variance_pct}%</span></td>
				<td class="num">${format_currency(m.cost)}</td></tr>`;
		}).join('');
		$('#bb-materials').html(mrows ? `<table><thead><tr><th>Item</th><th class="num">Target</th>
			<th class="num">Actual</th><th class="num">Var</th><th class="num">Cost</th></tr></thead>
			<tbody>${mrows}</tbody></table>` : '<div class="empty">No consumption recorded.</div>');
	}
}

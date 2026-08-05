frappe.pages['rmc-control-tower'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper, title: 'RMC Control Tower', single_column: true,
	});
	new ControlTower(page);
};

class ControlTower {
	constructor(page) {
		this.page = page;
		this.$body = $(page.body);
		this.days = 7;
		this.$body.html(`<div class="rmcp">
			<div class="hero" id="ct-hero"><h2>Loading…</h2></div>
			<div class="grid">
				<div class="card" style="grid-column:span 2"><h4>Produced vs dispatched</h4><div id="ct-trend"></div></div>
				<div class="card"><h4>Grade mix</h4><div id="ct-grades"></div></div>
			</div>
			<div class="grid" style="margin-top:14px">
				<div class="card"><h4>Needs attention</h4><div id="ct-alerts"></div></div>
				<div class="card" style="grid-column:span 2"><h4>Jump to</h4><div id="ct-links"></div></div>
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
		this.page.add_field({
			fieldtype: 'Select', fieldname: 'days', label: __('Period'),
			options: ['7', '14', '30'], default: '7',
			change: () => { this.days = this.page.fields_dict.days.get_value(); this.refresh(); },
		});
		this.page.set_primary_action(__('Refresh'), () => this.refresh(), 'refresh');
		this.refresh();
	}

	refresh() {
		frappe.call({ method: 'rmc.dashboard.control_tower', args: { days: this.days } })
			.then((r) => this.draw(r.message || {}));
	}

	draw(d) {
		const t = d.today || {};
		$('#ct-hero').html(`
			<h2>${frappe.utils.escape_html(d.plant || 'RMC Plant')}</h2>
			<div class="sub">${d.period ? d.period.from + ' to ' + d.period.to : ''}</div>
			<div class="strip">
				<div class="stat"><div class="n">${t.produced || 0}</div><div class="l">Produced today m³</div></div>
				<div class="stat"><div class="n">${t.dispatched || 0}</div><div class="l">Dispatched m³</div></div>
				<div class="stat"><div class="n">${t.trips || 0}</div><div class="l">Trips</div></div>
				<div class="stat"><div class="n">${format_currency(t.value || 0)}</div><div class="l">Value</div></div>
				<div class="stat"><div class="n">${d.open_orders || 0}</div><div class="l">Open orders</div></div>
				<div class="stat"><div class="n">${d.pending_m3 || 0}</div><div class="l">Pending m³</div></div>
			</div>`);

		const rows = (d.series || []).map(s => `<tr>
			<td>${frappe.datetime.str_to_user(s.date)}</td>
			<td class="num">${s.produced}</td><td class="num">${s.dispatched}</td>
			<td class="num">${s.trips}</td><td class="num">${format_currency(s.value)}</td></tr>`).join('');
		$('#ct-trend').html(`<table><thead><tr><th>Date</th><th class="num">Produced m³</th>
			<th class="num">Dispatched m³</th><th class="num">Trips</th><th class="num">Value</th></tr></thead>
			<tbody>${rows}</tbody></table>`);

		const total = (d.grades || []).reduce((a, g) => a + g.qty, 0) || 1;
		$('#ct-grades').html((d.grades || []).map(g => `
			<div style="margin-bottom:8px">
				<div style="display:flex;justify-content:space-between;font-size:12.5px">
					<b>${g.grade}</b><span>${g.qty} m³</span></div>
				<div class="bar"><span style="width:${Math.round(100 * g.qty / total)}%"></span></div>
			</div>`).join('') || '<div class="empty">No production in this period.</div>');

		const alert = (label, n, route) => `<tr><td>${label}</td>
			<td class="num"><span class="pill ${n ? 'bad' : 'ok'}">${n}</span></td>
			<td><a href="${route}">open</a></td></tr>`;
		$('#ct-alerts').html(`<table><tbody>
			${alert('Silos below alert level', d.low_silos, '/app/silo')}
			${alert('Open breakdowns', d.open_breakdowns, '/app/breakdown-log')}
			${alert('Failed cube tests', d.failed_cubes, '/app/cube-test?result=Fail')}
			${alert('Maintenance due', d.maintenance_due, '/app/rmc-maintenance-task')}
		</tbody></table>`);

		$('#ct-links').html(`
			<a class="btn btn-default btn-sm" href="/app/rmc-batch-board">Batching Board</a>
			<a class="btn btn-default btn-sm" href="/app/rmc-dispatch-board">Dispatch Board</a>
			<a class="btn btn-default btn-sm" href="/app/rmc-silo-board">Silo &amp; Stock</a>
			<a class="btn btn-default btn-sm" href="/app/rmc-quality-board">Quality</a>
			<a class="btn btn-default btn-sm" href="/app/query-report/Daily Production Summary">Production report</a>
			<a class="btn btn-default btn-sm" href="/app/query-report/Dispatch Register">Dispatch report</a>`);
	}
}

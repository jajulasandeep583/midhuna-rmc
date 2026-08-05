frappe.pages['rmc-quality-board'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper, title: 'Quality Board', single_column: true,
	});
	new QualityBoard(page);
};

class QualityBoard {
	constructor(page) {
		this.page = page;
		this.$body = $(page.body);
		this.$body.html(`<div class="rmcp">
			<div class="hero" id="qb-hero"><h2>Loading…</h2></div>
			<div class="grid">
				<div class="card"><h4>Pass rate by grade</h4><div id="qb-grades"></div></div>
				<div class="card"><h4>Failed cubes</h4><div id="qb-fails"></div></div>
				<div class="card"><h4>28-day break pending</h4><div id="qb-pending"></div></div>
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
		this.page.set_primary_action(__('New Cube Test'), () => frappe.new_doc('Cube Test'));
		this.refresh();
	}

	refresh() {
		frappe.call({ method: 'rmc.dashboard.quality_board' })
			.then((r) => this.draw(r.message || {}));
	}

	draw(d) {
		$('#qb-hero').html(`<h2>Quality — last 90 days</h2>
			<div class="strip">
				<div class="stat"><div class="n">${d.total_tests || 0}</div><div class="l">Cube tests</div></div>
				<div class="stat"><div class="n">${d.total_fails || 0}</div><div class="l">Failed</div></div>
				<div class="stat"><div class="n">${(d.pending_28day || []).length}</div><div class="l">Awaiting 28-day break</div></div>
			</div>`);

		$('#qb-grades').html((d.by_grade || []).length ? `<table>
			<thead><tr><th>Grade</th><th class="num">Tests</th><th class="num">Pass %</th>
			<th class="num">Avg MPa</th><th class="num">Of required</th></tr></thead>
			<tbody>${d.by_grade.map(g => `<tr><td><b>${g.grade}</b></td>
				<td class="num">${g.tests}</td>
				<td class="num"><span class="pill ${g.pass_rate === 100 ? 'ok' : 'warn'}">${g.pass_rate}%</span></td>
				<td class="num">${g.avg_strength}</td><td class="num">${g.avg_pct}%</td></tr>`).join('')}
			</tbody></table>` : '<div class="empty">No tests recorded.</div>');

		$('#qb-fails').html((d.fails || []).length ? `<table>
			<thead><tr><th>Test</th><th>Cast</th><th>Grade</th><th class="num">Got</th><th class="num">Needed</th></tr></thead>
			<tbody>${d.fails.map(f => `<tr>
				<td><a href="/app/cube-test/${encodeURIComponent(f.name)}">${f.name}</a></td>
				<td>${frappe.datetime.str_to_user(f.casting_date)}</td>
				<td>${f.grade}</td><td class="num">${f.avg_strength_mpa}</td>
				<td class="num">${Number(f.required_strength_mpa).toFixed(1)}</td></tr>`).join('')}
			</tbody></table>` : '<div class="empty">No failures — good.</div>');

		$('#qb-pending').html((d.pending_28day || []).length ? `<table>
			<thead><tr><th>Challan</th><th>Cast</th><th>Grade</th><th class="num">m³</th></tr></thead>
			<tbody>${d.pending_28day.map(p => `<tr>
				<td><a href="/app/delivery-challan/${encodeURIComponent(p.name)}">${p.name}</a></td>
				<td>${frappe.datetime.str_to_user(p.challan_date)}</td>
				<td>${p.grade}</td><td class="num">${p.qty_m3}</td></tr>`).join('')}
			</tbody></table>` : '<div class="empty">Nothing pending.</div>');
	}
}

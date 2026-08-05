frappe.pages['rmc-silo-board'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper, title: 'Silo & Stock Board', single_column: true,
	});
	new SiloBoard(page);
};

class SiloBoard {
	constructor(page) {
		this.page = page;
		this.$body = $(page.body);
		this.$body.html(`<div class="rmcp">
			<div class="hero" id="sb-hero"><h2>Silo &amp; Stock</h2>
				<div class="sub">Level, burn rate and days of cover for every silo and yard</div></div>
			<div class="card"><div id="sb-table"></div></div></div>` + `
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
		this.page.set_primary_action(__('New Inward'), () => frappe.new_doc('Material Inward'));
		this.page.add_menu_item(__('Refresh'), () => this.refresh());
		this.refresh();
	}

	refresh() {
		frappe.call({ method: 'rmc.dashboard.silo_board' }).then((r) => this.draw(r.message || []));
	}

	draw(rows) {
		const low = rows.filter(r => r.low).length;
		$('#sb-hero .sub').html(
			`Level, burn rate and days of cover · <b>${rows.length}</b> silos · ` +
			`<b>${low}</b> below alert level`);
		$('#sb-table').html(`<table>
			<thead><tr><th>Silo / Yard</th><th>Material</th><th class="num">Stock</th>
			<th class="num">Capacity</th><th style="width:24%">Level</th>
			<th class="num">Burn / day</th><th class="num">Days cover</th><th>Alert</th></tr></thead>
			<tbody>${rows.map(r => `<tr>
				<td>${frappe.utils.escape_html(r.silo)}</td>
				<td>${r.material}</td>
				<td class="num">${r.stock_mt}</td>
				<td class="num">${r.capacity_mt}</td>
				<td><div class="bar ${r.low ? 'low' : ''}">
					<span style="width:${Math.min(100, r.filled_pct)}%"></span></div>
					<span style="font-size:11px">${r.filled_pct}%</span></td>
				<td class="num">${r.daily_burn_mt}</td>
				<td class="num">${r.days_cover === null ? '—' : r.days_cover}</td>
				<td><span class="pill ${r.low ? 'bad' : 'ok'}">${r.low ? 'REORDER' : 'OK'}</span></td>
			</tr>`).join('')}</tbody></table>`);
	}
}

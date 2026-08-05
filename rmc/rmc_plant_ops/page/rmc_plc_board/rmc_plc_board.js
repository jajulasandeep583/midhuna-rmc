frappe.pages['rmc-plc-board'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper, title: 'Live PLC Board', single_column: true,
	});
	new PLCBoard(page);
};

class PLCBoard {
	constructor(page) {
		this.page = page;
		this.$body = $(page.body);
		this.$body.html(`<div class="rmcplc">
			<div class="hero" id="plc-hero"><h2>Connecting…</h2></div>
			<div id="plc-alarms"></div>
			<div id="plc-groups"></div>
			<div class="grid" id="plc-traces" style="margin-top:14px"></div>
		</div>` + STYLE);

		this.plant_f = this.page.add_field({
			fieldtype: 'Link', fieldname: 'plant', label: __('Plant'),
			options: 'RMC Plant', change: () => this.refresh(),
		});
		this.page.set_primary_action(__('Refresh'), () => this.refresh(), 'refresh');
		this.page.add_menu_item(__('Open the public wall screen'), () => {
			window.open('/rmc/plc?plant=' + encodeURIComponent(this.plant_f.get_value() || ''),
				'_blank');
		});
		this.page.add_menu_item(__('Tag list'), () => frappe.set_route('List', 'RMC PLC Tag'));
		this.page.add_menu_item(__('Reading history'), () =>
			frappe.set_route('List', 'RMC PLC Reading'));

		frappe.db.get_list('RMC Plant', { filters: { is_active: 1 }, fields: ['name'], limit: 1 })
			.then((r) => {
				if (r && r.length) this.plant_f.set_value(r[0].name);
				else this.refresh();
			});

		// a wall screen must not go stale
		this.timer = setInterval(() => this.refresh(), 60000);
		$(page.wrapper).on('remove', () => clearInterval(this.timer));
	}

	refresh() {
		frappe.call({ method: 'rmc.plc.live', args: { plant: this.plant_f.get_value() || null } })
			.then((r) => this.draw(r.message || []));
	}

	gauge(t) {
		const pct = Math.max(0, Math.min(100, t.pct || 0));
		const cls = t.alarm ? 'bad' : (pct < 25 ? 'warn' : 'ok');
		const val = (t.value === null || t.value === undefined) ? '—' : t.value;
		// levels get a vertical silo, everything else a horizontal bar
		if (t.category === 'Silo Level') {
			return `<div class="tag ${t.alarm ? 'alarm' : ''}">
				<div class="silo">
					<div class="fill ${cls}" style="height:${pct}%"></div>
					<span>${pct}%</span>
				</div>
				<div class="meta">
					<div class="nm">${frappe.utils.escape_html(t.tag_name)}</div>
					<div class="vv">${val}<small>${t.unit || ''}</small></div>
					<div class="cd">${t.tag_code}</div>
				</div>
			</div>`;
		}
		if (t.category === 'Status') {
			const on = Number(t.value) >= 1;
			return `<div class="tag">
				<div class="lamp ${on ? 'on' : ''}"></div>
				<div class="meta">
					<div class="nm">${frappe.utils.escape_html(t.tag_name)}</div>
					<div class="vv">${on ? 'ON' : 'OFF'}</div>
					<div class="cd">${t.tag_code}</div>
				</div>
			</div>`;
		}
		return `<div class="tag wide ${t.alarm ? 'alarm' : ''}">
			<div class="nm">${frappe.utils.escape_html(t.tag_name)}</div>
			<div class="vv">${val}<small>${t.unit || ''}</small></div>
			<div class="bar"><span class="${cls}" style="width:${pct}%"></span></div>
			<div class="cd">${t.tag_code}${t.quality !== 'Good' ? ' · ' + t.quality : ''}</div>
		</div>`;
	}

	draw(tags) {
		const alarms = tags.filter((t) => t.alarm);
		const run = tags.find((t) => t.tag_code === 'PLANT_RUN');
		const running = run && Number(run.value) >= 1;
		const last = tags.map((t) => t.reading_time).filter(Boolean).sort().pop();

		$('#plc-hero').html(`
			<h2>${frappe.utils.escape_html(this.plant_f.get_value() || 'No plant')}
				<span class="pill ${running ? 'ok' : 'mute'}">${running ? 'RUNNING' : 'IDLE'}</span></h2>
			<div class="strip">
				<div class="stat"><div class="n">${tags.length}</div><div class="l">Live tags</div></div>
				<div class="stat"><div class="n">${alarms.length}</div><div class="l">Out of band</div></div>
				<div class="stat"><div class="n">${last ? frappe.datetime.str_to_user(last) : '—'}</div>
					<div class="l">Last signal</div></div>
				<div class="stat"><div class="n">15 min</div><div class="l">Poll interval</div></div>
			</div>`);

		$('#plc-alarms').html(alarms.length ? `<div class="card alarmcard">
			<h4>Out of band right now</h4>
			<table><thead><tr><th>Signal</th><th class="num">Value</th><th class="num">Limit</th></tr></thead>
			<tbody>${alarms.map((a) => `<tr>
				<td>${frappe.utils.escape_html(a.tag_name)} <span class="cd">${a.tag_code}</span></td>
				<td class="num"><span class="pill bad">${a.value} ${a.unit || ''}</span></td>
				<td class="num">${a.warn_low ? 'min ' + a.warn_low : ''}
					${a.warn_high ? 'max ' + a.warn_high : ''}</td></tr>`).join('')}
			</tbody></table></div>` : '');

		const order = ['Status', 'Silo Level', 'Weigh Hopper', 'Motor', 'Process', 'Power', 'Counter'];
		const groups = {};
		tags.forEach((t) => { (groups[t.category] = groups[t.category] || []).push(t); });
		$('#plc-groups').html(order.filter((c) => groups[c]).map((c) => `
			<div class="card"><h4>${c}</h4>
				<div class="tags">${groups[c].map((t) => this.gauge(t)).join('')}</div></div>`).join(''));

		// 24-hour traces for the four an operator actually watches
		const watch = ['PLANT_KW', 'MIXER_CURRENT', 'CEM_SILO1_LVL', 'EB_VOLTAGE'];
		$('#plc-traces').empty();
		watch.forEach((code) => {
			const tag = tags.find((t) => t.tag_code === code);
			if (!tag) return;
			frappe.call({ method: 'rmc.plc.trend', args: { tag: tag.name, hours: 24 } })
				.then((r) => {
					const pts = r.message || [];
					if (!pts.length) return;
					const peak = Math.max(...pts.map((p) => p.value)) || 1;
					$('#plc-traces').append(`<div class="card">
						<h4>${frappe.utils.escape_html(tag.tag_name)} — last 24 hours</h4>
						<div style="font-size:19px;font-weight:800">${tag.value}
							<small style="font-size:12px;opacity:.6">${tag.unit || ''} now · peak ${peak.toFixed(1)}</small></div>
						<div class="trace">${pts.map((p) =>
							`<i title="${p.reading_time}: ${p.value}" style="height:${Math.round(100 * p.value / peak)}%"></i>`).join('')}</div>
					</div>`);
				});
		});
	}
}

const STYLE = `
<style>
	.rmcplc{max-width:1240px;margin:0 auto}
	.rmcplc .hero{background:linear-gradient(120deg,#06283d,#0EA5E9);color:#fff;
		border-radius:14px;padding:18px 22px;margin-bottom:14px}
	.rmcplc .hero h2{margin:0;font-size:20px;font-weight:800;display:flex;gap:10px;align-items:center}
	.rmcplc .strip{display:flex;gap:26px;flex-wrap:wrap;margin-top:14px}
	.rmcplc .stat .n{font-size:22px;font-weight:800;line-height:1.15}
	.rmcplc .stat .l{font-size:11px;opacity:.85;text-transform:uppercase;letter-spacing:.6px}
	.rmcplc .card{background:var(--card-bg,#fff);border:1px solid var(--border-color,#e2e6ea);
		border-radius:12px;padding:15px 17px;margin-bottom:13px}
	.rmcplc .card h4{margin:0 0 12px;font-size:12px;text-transform:uppercase;letter-spacing:.7px;
		color:var(--text-muted,#6c7680)}
	.rmcplc .alarmcard{border-left:4px solid #DC2626}
	.rmcplc .tags{display:grid;grid-template-columns:repeat(auto-fit,minmax(178px,1fr));gap:11px}
	.rmcplc .tag{display:flex;gap:11px;align-items:center;border:1px solid var(--border-color,#e6eaee);
		border-radius:10px;padding:10px 12px}
	.rmcplc .tag.wide{display:block}
	.rmcplc .tag.alarm{border-color:#DC2626;box-shadow:inset 3px 0 0 #DC2626}
	.rmcplc .nm{font-size:11.5px;color:var(--text-muted,#6c7680);text-transform:uppercase;
		letter-spacing:.5px;line-height:1.25}
	.rmcplc .vv{font-size:19px;font-weight:800;margin:2px 0 3px}
	.rmcplc .vv small{font-size:11.5px;font-weight:600;opacity:.6;margin-left:3px}
	.rmcplc .cd{font-size:10.5px;color:var(--text-muted,#8b96a2);font-family:ui-monospace,monospace}
	.rmcplc .silo{position:relative;width:34px;height:64px;border:2px solid var(--border-color,#c9d2db);
		border-radius:6px 6px 3px 3px;overflow:hidden;flex:none;background:var(--bg-light-gray,#f3f5f8)}
	.rmcplc .silo .fill{position:absolute;bottom:0;left:0;right:0;transition:height .4s}
	.rmcplc .silo .fill.ok{background:#1a7f4b}.rmcplc .silo .fill.warn{background:#c98a12}
	.rmcplc .silo .fill.bad{background:#d93a2b}
	.rmcplc .silo span{position:absolute;inset:0;display:grid;place-items:center;font-size:11px;
		font-weight:800;color:#0b1b28;text-shadow:0 1px 2px rgba(255,255,255,.7)}
	.rmcplc .lamp{width:26px;height:26px;border-radius:50%;flex:none;background:#9aa6b2;
		box-shadow:0 0 0 4px rgba(154,166,178,.18)}
	.rmcplc .lamp.on{background:#21c05b;box-shadow:0 0 0 4px rgba(33,192,91,.22)}
	.rmcplc .bar{height:7px;border-radius:4px;background:var(--bg-light-gray,#eef1f5);overflow:hidden;
		margin:4px 0}
	.rmcplc .bar span{display:block;height:100%}
	.rmcplc .bar span.ok{background:#2563EB}.rmcplc .bar span.warn{background:#c98a12}
	.rmcplc .bar span.bad{background:#d93a2b}
	.rmcplc .pill{display:inline-block;padding:2px 11px;border-radius:11px;font-size:11px;font-weight:800}
	.rmcplc .pill.ok{background:#e7f7ec;color:#12793d}
	.rmcplc .pill.bad{background:#fdeaea;color:#b3261e}
	.rmcplc .pill.mute{background:rgba(255,255,255,.22);color:#fff}
	.rmcplc .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:13px}
	.rmcplc .trace{display:flex;align-items:flex-end;gap:1px;height:58px;margin-top:8px}
	.rmcplc .trace i{flex:1;min-height:1px;background:#0EA5E9;border-radius:1px 1px 0 0;opacity:.8}
	.rmcplc table{width:100%;font-size:13px;border-collapse:collapse}
	.rmcplc th{text-align:left;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;
		color:var(--text-muted,#6c7680);padding:4px 6px;border-bottom:1px solid var(--border-color,#e2e6ea)}
	.rmcplc td{padding:5px 6px;border-bottom:1px solid var(--border-color,#f0f2f4)}
	.rmcplc .num{text-align:right;font-variant-numeric:tabular-nums}
</style>`;

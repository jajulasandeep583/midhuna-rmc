frappe.pages['rmc-guide'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper, title: 'How to Use RMC', single_column: true,
	});
	$(page.body).html(`<div class="rmcg"><div class="hero"><h2>How to Use RMC Plant Smart ERP</h2><div class="sub">MIDHUNATECH · Monitor · Manage · Produce · Deliver — the whole plant, one screen at a time</div></div><div class="toc"><a href="#start"><span>1. Start here — what this app is</span><small>Ready mix concrete, from raw material inward to the signed delivery challan.</small></a><a href="#roles"><span>2. Who does what</span><small>Five roles, five daily jobs. Each login opens on the workspace it needs.</small></a><a href="#setup"><span>3. One-time setup</span><small>Do this once, in this order, before the first pour.</small></a><a href="#inward"><span>4. Raw material in — the weighbridge</span><small>Every truck of cement, sand, aggregate, fly ash or admixture.</small></a><a href="#order"><span>5. The customer order</span><small>What was booked, and the pour schedule it must be delivered against.</small></a><a href="#batch"><span>6. Batching the concrete</span><small>The shift's core screen — recipe in, actual consumption out.</small></a><a href="#dispatch"><span>7. Dispatch and the delivery challan</span><small>The document that travels with every truck.</small></a><a href="#quality"><span>8. Quality — cubes and slump</span><small>Strength against what the grade requires, decided for you.</small></a><a href="#plant"><span>9. The plant itself</span><small>Running time, breakdowns, maintenance and power.</small></a><a href="#boards"><span>10. The boards</span><small>Seven screens that answer a question without you building a report.</small></a><a href="#reports"><span>11. Reports</span><small>Twenty script reports, each with a date range and its own filters.</small></a><a href="#rules"><span>12. Rules the app enforces</span><small>You cannot get these wrong — the app stops you.</small></a><a href="#month"><span>13. Month end</span><small>Five checks, in order, and the books agree.</small></a></div><section id="start"><h3><span class="step">1</span>Start here — what this app is</h3><p class="lede">Ready mix concrete, from raw material inward to the signed delivery challan.</p>
<p>RMC Plant Smart ERP runs your whole plant on top of standard ERPNext. Three things
matter before you click anything:</p>
<ul>
	<li><b class="k">Nothing is typed twice.</b> Delivered quantity, pending quantity, order
		status, trip cycle time, batch cost, cube pass/fail and silo level are all
		<i>derived</i> by the system. If a number looks wrong, fix the document it came from.</li>
	<li><b class="k">Every silo is a warehouse.</b> The stock balance in that warehouse
		<i>is</i> the silo level — there is no separate stock register to reconcile.</li>
	<li><b class="k">The paperwork writes itself.</b> An inward raises the purchase receipt,
		a batch raises the stock entry, a challan raises the sales invoice.</li>
</ul>
<div class="flow">Material Inward  --submit-->  Purchase Receipt   (stock into the silo)
Concrete Order   ------------.
Batch Production --submit-->  Stock Entry       (raw out, concrete in)
Delivery Challan --submit-->  Sales Invoice     (concrete out, revenue booked)
                              Concrete Order    (delivered / pending recomputed)</div>
<div class="btns">
	<a class="btn btn-primary btn-sm" href="/app/rmc-manage">Management view</a>
	<a class="btn btn-default btn-sm" href="/app/rmc-control-tower">Control Tower</a>
</div></section><section id="roles"><h3><span class="step">2</span>Who does what</h3><p class="lede">Five roles, five daily jobs. Each login opens on the workspace it needs.</p>
<table>
	<tr><th>Role</th><th>Opens</th><th>Does</th></tr>
	<tr><td><b class="k">RMC Manager</b></td><td>Management, Control Tower</td>
		<td>Rates, orders, MIS, margins, approvals</td></tr>
	<tr><td><b class="k">Plant Operator</b></td><td>Batching Board</td>
		<td>Batches concrete, records actual consumption, logs plant status</td></tr>
	<tr><td><b class="k">Dispatch Incharge</b></td><td>Dispatch Board</td>
		<td>Allocates trucks, raises challans, closes trips</td></tr>
	<tr><td><b class="k">Quality Engineer</b></td><td>Quality Board</td>
		<td>Cube tests, slump, mix designs</td></tr>
	<tr><td><b class="k">RMC Accounts</b></td><td>Management</td>
		<td>Invoices, supplier bills, receivables</td></tr>
</table>
<div class="note">Every role also sees the ERPNext documents its work creates —
a manager can open the invoice their challan raised, an operator the stock entry
their batch posted.</div></section><section id="setup"><h3><span class="step">3</span>One-time setup</h3><p class="lede">Do this once, in this order, before the first pour.</p>
<ol>
	<li><b class="k">RMC Plant</b> — name, capacity m³/hr, and the two warehouses
		(raw material parent, finished concrete).</li>
	<li><b class="k">Concrete Grade</b> — M10 to M60 ship ready with strength, typical
		application and rate. Each grade automatically gets a sellable item (<i>RMC-M25</i>).</li>
	<li><b class="k">Mix Design</b> — the per-m³ recipe: cement, fly ash, sand, 20 mm,
		10 mm, admixture, water. The app checks the batched weight lands in the normal
		1800–2800 kg/m³ band and works out the water/cement ratio and cost per m³.</li>
	<li><b class="k">Silo</b> — one per silo, yard or tank, each pointing at its own
		warehouse, with a capacity and a low-level alert.</li>
	<li><b class="k">Transit Mixer</b> — vehicle number, capacity, ownership, default
		driver, fitness and insurance validity.</li>
	<li><b class="k">Construction Site</b> — customer, address and <i>distance from plant</i>
		(this drives expected cycle time).</li>
	<li><b class="k">RMC Settings</b> — default plant and the two automation switches:
		auto sales invoice on challan, auto stock entry on batch.</li>
</ol>
<div class="btns">
	<a class="btn btn-default btn-sm" href="/app/rmc-plant">Plant</a>
	<a class="btn btn-default btn-sm" href="/app/concrete-grade">Grades</a>
	<a class="btn btn-default btn-sm" href="/app/mix-design">Mix designs</a>
	<a class="btn btn-default btn-sm" href="/app/silo">Silos</a>
	<a class="btn btn-default btn-sm" href="/app/transit-mixer">Mixers</a>
	<a class="btn btn-default btn-sm" href="/app/construction-site">Sites</a>
</div></section><section id="inward"><h3><span class="step">4</span>Raw material in — the weighbridge</h3><p class="lede">Every truck of cement, sand, aggregate, fly ash or admixture.</p>
<ol>
	<li>Open <b class="k">Material Inward</b> (or the New Inward button on the Silo board).</li>
	<li>Pick the supplier, the item and the <b class="k">silo</b> it is unloaded into —
		the silo sets the receiving warehouse for you.</li>
	<li>Enter <b class="k">gross</b> and <b class="k">tare</b> weight; net is calculated
		and must be positive.</li>
	<li>Enter the rate. Amount is calculated.</li>
	<li>Set the <b class="k">inward time</b> — the stock posts at that moment, so material
		is in the silo before the shift that consumes it.</li>
	<li>Submit. A <b class="k">Purchase Receipt</b> is raised: stock lands in the silo and
		the supplier liability is booked.</li>
</ol>
<div class="note rule">Untick <i>Quality Accepted</i> to record a rejection — rejected
material cannot be submitted into stock at all.</div>
<div class="btns">
	<a class="btn btn-primary btn-sm" href="/app/material-inward/new">New inward</a>
	<a class="btn btn-default btn-sm" href="/app/rmc-silo-board">Silo &amp; Stock board</a>
	<a class="btn btn-default btn-sm" href="/app/query-report/Material Inward Register">Inward register</a>
</div></section><section id="order"><h3><span class="step">5</span>The customer order</h3><p class="lede">What was booked, and the pour schedule it must be delivered against.</p>
<ol>
	<li>Open <b class="k">Concrete Order</b>. Pick customer, construction site, grade,
		quantity in m³, rate and the required dates.</li>
	<li>Add <b class="k">pour schedule</b> rows (date, time slot, quantity) for a staged pour.</li>
	<li>Tick <i>Concrete Pump Required</i> if a pump must go with it.</li>
	<li>Submit. The order opens and starts accepting deliveries.</li>
</ol>
<p>Delivered and pending quantities are <b class="k">never typed</b> — they are recomputed
from the submitted challans, and the status moves Open → In Progress → Completed by itself.</p>
<div class="note rule">Guard rails: the site must belong to the customer, the schedule may
not exceed the order, and a customer whose <b>RMC Credit Status</b> is <i>Hold</i> cannot be
given a new order at all.</div>
<div class="btns">
	<a class="btn btn-primary btn-sm" href="/app/concrete-order/new">New order</a>
	<a class="btn btn-default btn-sm" href="/app/rmc-order-360">Order 360</a>
	<a class="btn btn-default btn-sm" href="/app/query-report/Customer Order Status">Order status</a>
</div></section><section id="batch"><h3><span class="step">6</span>Batching the concrete</h3><p class="lede">The shift's core screen — recipe in, actual consumption out.</p>
<ol>
	<li>Open the <b class="k">Batching Board</b> and hit New Batch (or Batch Production directly).</li>
	<li>Date, shift, plant, grade and mix design.</li>
	<li>Link the <b class="k">Concrete Order</b> the pour belongs to — leave blank for
		stock production.</li>
	<li>Enter the produced quantity in m³. The material grid fills itself from the recipe:
		<b class="k">target</b> quantity per item.</li>
	<li>Type what the plant actually weighed in the <b class="k">actual</b> column.
		Variance %% appears per line, so over- or under-dosing is visible immediately.</li>
	<li>Submit. A <b class="k">Stock Entry (Manufacture)</b> posts: every raw material leaves
		its own silo warehouse, and the finished concrete arrives valued at the real batch cost.</li>
</ol>
<div class="note warn">The mix design must belong to the batch's grade — the app refuses a
mismatch, which is what stops an M20 recipe being poured against an M40 order.</div>
<div class="btns">
	<a class="btn btn-primary btn-sm" href="/app/rmc-batch-board">Batching board</a>
	<a class="btn btn-default btn-sm" href="/app/query-report/Material Consumption vs Recipe">Consumption vs recipe</a>
</div></section><section id="dispatch"><h3><span class="step">7</span>Dispatch and the delivery challan</h3><p class="lede">The document that travels with every truck.</p>
<ol>
	<li>Open the <b class="k">Dispatch Board</b> → New Challan.</li>
	<li>Pick the order — customer, site, grade and rate fill in. Enter the load quantity,
		the transit mixer and driver, and the batch it was loaded from.</li>
	<li>Record <b class="k">dispatch time</b> when it leaves; then site arrival, unloading
		end and plant return as the trip proceeds. <b class="k">Cycle time</b> is computed
		from dispatch → return — the core RMC productivity number.</li>
	<li>Record <b class="k">slump at site</b> and temperature; tick <i>Cubes Taken</i> if
		the QC engineer sampled the load.</li>
	<li>Move status Dispatched → Delivered → Returned. The truck's own status follows:
		<i>On Trip</i> on dispatch, <i>Available</i> when it returns.</li>
	<li>Submit raises the <b class="k">Sales Invoice</b> (with stock update): concrete leaves
		the finished warehouse and revenue is booked in one step.</li>
</ol>
<div class="note rule">A challan can never deliver more than the order has left. This single
rule prevents the most common RMC billing dispute.</div>
<p><b class="k">Printing:</b> use the <i>RMC Delivery Challan</i> format — customer, site,
grade, quantity, vehicle, driver, times, a QR code for site verification and a signature
block. Print, PDF, e-mail or WhatsApp it.</p>
<div class="btns">
	<a class="btn btn-primary btn-sm" href="/app/rmc-dispatch-board">Dispatch board</a>
	<a class="btn btn-default btn-sm" href="/app/query-report/Dispatch Register">Dispatch register</a>
	<a class="btn btn-default btn-sm" href="/app/query-report/Vehicle Utilisation and Trips">Vehicle utilisation</a>
</div></section><section id="quality"><h3><span class="step">8</span>Quality — cubes and slump</h3><p class="lede">Strength against what the grade requires, decided for you.</p>
<ol>
	<li>Open the <b class="k">Quality Board</b> → New Cube Test.</li>
	<li>Link the batch; grade and casting date come with it.</li>
	<li>Choose the age (7 / 14 / 28 days) and enter the achieved strength.</li>
</ol>
<p>Pass or fail is derived, not typed: IS 456 expects <b class="k">65%%</b> of the
characteristic strength at 7 days and <b class="k">100%%</b> at 28. A failed cube raises a
red quality alert on submit.</p>
<p>The Quality Board also lists loads that were sampled but whose <b class="k">28-day break
is still pending</b>, so nothing quietly goes untested.</p>
<div class="btns">
	<a class="btn btn-primary btn-sm" href="/app/rmc-quality-board">Quality board</a>
	<a class="btn btn-default btn-sm" href="/app/query-report/Cube Test Register">Cube test register</a>
</div></section><section id="plant"><h3><span class="step">9</span>The plant itself</h3><p class="lede">Running time, breakdowns, maintenance and power.</p>
<ul>
	<li><b class="k">Plant Status Log</b> — running / idle / breakdown / stopped blocks with
		from–to times. A reason is mandatory for breakdown and stopped. This is what
		<i>availability %%</i> is calculated from.</li>
	<li><b class="k">Breakdown Log</b> — equipment, reported and resolved time (downtime
		computed), reason, action taken, repair cost. A transit-mixer breakdown puts that
		vehicle <i>Under Maintenance</i> automatically.</li>
	<li><b class="k">RMC Maintenance Task</b> — the preventive schedule; rows flip to
		<i>Due</i> and <i>Overdue</i> by themselves every night.</li>
	<li><b class="k">Power Log</b> — EB units and hours, DG units and hours, diesel litres
		and cost. The report divides it back to units per m³.</li>
</ul>
<div class="btns">
	<a class="btn btn-default btn-sm" href="/app/plant-status-log">Status log</a>
	<a class="btn btn-default btn-sm" href="/app/breakdown-log">Breakdowns</a>
	<a class="btn btn-default btn-sm" href="/app/query-report/Plant Availability and Downtime">Availability</a>
</div></section><section id="boards"><h3><span class="step">10</span>The boards</h3><p class="lede">Seven screens that answer a question without you building a report.</p>
<table>
	<tr><th>Board</th><th>Answers</th></tr>
	<tr><td><a href="/app/rmc-manage"><b>Management</b></a></td>
		<td>What did we sell, buy, make and hold — and what is still owed to us?</td></tr>
	<tr><td><a href="/app/rmc-control-tower"><b>Control Tower</b></a></td>
		<td>How is today going, and what needs attention right now?</td></tr>
	<tr><td><a href="/app/rmc-live-dashboard"><b>Live Plant Dashboard</b></a></td>
		<td>Wall screen: plant status, silo levels, order book — refreshes itself.</td></tr>
	<tr><td><a href="/app/rmc-batch-board"><b>Batching Board</b></a></td>
		<td>What was batched today and how close was it to the recipe?</td></tr>
	<tr><td><a href="/app/rmc-dispatch-board"><b>Dispatch Board</b></a></td>
		<td>Which trucks are out, which are back, how long is a cycle?</td></tr>
	<tr><td><a href="/app/rmc-silo-board"><b>Silo &amp; Stock</b></a></td>
		<td>How full is each silo, how fast is it burning, how many days are left?</td></tr>
	<tr><td><a href="/app/rmc-quality-board"><b>Quality</b></a></td>
		<td>Pass rate by grade, failures, and 28-day breaks still pending.</td></tr>
	<tr><td><a href="/app/rmc-order-360"><b>Order 360</b></a></td>
		<td>One order end to end: batches, loads, cubes, invoices, %% complete.</td></tr>
</table>
<div class="note">Every board has filters in its toolbar — date, plant, shift, grade,
customer, status. Change one and the whole board reloads.</div></section><section id="reports"><h3><span class="step">11</span>Reports</h3><p class="lede">Twenty script reports, each with a date range and its own filters.</p>
<table>
	<tr><th>Report</th><th>Answers</th></tr>
	<tr><td>Daily Production Summary</td><td>m³ per day, shift and grade, with cost per m³</td></tr>
	<tr><td>Batch Register</td><td>Every batch with order, customer, operator, stock entry</td></tr>
	<tr><td>Material Consumption vs Recipe</td><td>Where a load cell drifted or material leaked</td></tr>
	<tr><td>Production Target vs Actual</td><td>Ordered vs delivered, order by order</td></tr>
	<tr><td>Cube Test Register</td><td>Required vs achieved strength, pass/fail</td></tr>
	<tr><td>Material Inward Register</td><td>Every weighbridge ticket and its receipt</td></tr>
	<tr><td>Silo and Stock Status</td><td>Level, filled %%, alert, stock value</td></tr>
	<tr><td>Dispatch Register</td><td>Every load with cycle time, slump and invoice</td></tr>
	<tr><td>Customer Order Status</td><td>Per customer: ordered, delivered, pending</td></tr>
	<tr><td>Vehicle Utilisation and Trips</td><td>Trips, load factor, average cycle</td></tr>
	<tr><td>Customer Wise Sales</td><td>Value by customer and grade</td></tr>
	<tr><td>Plant Availability and Downtime</td><td>Running / idle / breakdown, availability %%</td></tr>
	<tr><td>Power and Diesel Consumption</td><td>EB and DG units, diesel, units per m³</td></tr>
	<tr><td>Breakdown and Maintenance Log</td><td>Every stoppage, downtime and repair cost</td></tr>
	<tr><td>Order Book and Pour Schedule</td><td>What is promised, and when</td></tr>
	<tr><td>Supplier Purchase Summary</td><td>What each supplier delivered and billed</td></tr>
	<tr><td>Driver Performance</td><td>Trips, m³ and cycle time by driver</td></tr>
	<tr><td>Slump Compliance</td><td>Slump against the mix design target</td></tr>
	<tr><td>Grade Profitability</td><td>Revenue minus material cost, per grade</td></tr>
	<tr><td>Monthly Plant Summary</td><td>The month on one line each</td></tr>
</table>
<div class="btns"><a class="btn btn-primary btn-sm" href="/app/rmc-reports">Open the report hub</a></div></section><section id="rules"><h3><span class="step">12</span>Rules the app enforces</h3><p class="lede">You cannot get these wrong — the app stops you.</p>
<ul>
	<li>A challan can never over-deliver its order.</li>
	<li>A batch's mix design must belong to the batch's grade.</li>
	<li>A customer on credit hold cannot be given a new order.</li>
	<li>Material that failed quality cannot be taken into stock.</li>
	<li>Gross weight must exceed tare; net is always gross − tare.</li>
	<li>Breakdown or stopped plant time needs a written reason.</li>
	<li>Cancelling a batch cancels its stock entry; cancelling a challan cancels its invoice.</li>
	<li>An order cannot be cancelled while its challans still stand.</li>
</ul></section><section id="month"><h3><span class="step">13</span>Month end</h3><p class="lede">Five checks, in order, and the books agree.</p>
<ol>
	<li><b class="k">Customer Order Status</b> — chase anything still Open or In Progress.</li>
	<li><b class="k">Material Consumption vs Recipe</b> — investigate any item beyond ±2%%.</li>
	<li><b class="k">Silo and Stock Status</b> — reconcile silo levels with the physical dip.</li>
	<li><b class="k">Plant Availability</b> — compare with the target in RMC Settings.</li>
	<li><b class="k">Customer Wise Sales</b> vs ERPNext's Accounts Receivable — they are the
		same invoices, so they must agree to the paisa.</li>
</ol>
<div class="note">The Management board shows revenue, material cost and gross margin for any
period you pick — start there, then drill down.</div></section></div>` + `
<style>
	.rmcg{max-width:1000px;margin:0 auto;font-size:14.5px;line-height:1.65}
	.rmcg .hero{background:linear-gradient(120deg,#0b2f5c,#12508f);color:#fff;
		border-radius:14px;padding:22px 24px;margin-bottom:16px}
	.rmcg .hero h2{margin:0;font-size:22px;font-weight:800}
	.rmcg .hero .sub{opacity:.85;font-size:13.5px;margin-top:4px}
	.rmcg .toc{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));
		gap:9px;margin-bottom:18px}
	.rmcg .toc a{display:block;text-decoration:none;border:1px solid var(--border-color,#e2e6ea);
		border-radius:10px;padding:10px 13px;font-size:13px;font-weight:650;color:inherit;
		background:var(--card-bg,#fff)}
	.rmcg .toc a:hover{border-color:#12508f}
	.rmcg .toc a small{display:block;font-weight:400;opacity:.65;font-size:11.5px;margin-top:2px}
	.rmcg section{background:var(--card-bg,#fff);border:1px solid var(--border-color,#e2e6ea);
		border-radius:12px;padding:18px 22px;margin-bottom:14px;scroll-margin-top:80px}
	.rmcg h3{margin:0 0 4px;font-size:17px;font-weight:800;display:flex;align-items:center}
	.rmcg h3 .step{display:inline-grid;place-items:center;width:26px;height:26px;flex:none;
		border-radius:8px;background:#12508f;color:#fff;font-size:13px;margin-right:10px}
	.rmcg .lede{color:var(--text-muted,#6c7680);margin:0 0 12px 36px;font-size:13.5px}
	.rmcg ol,.rmcg ul{margin:8px 0 8px 36px;padding-left:18px}
	.rmcg li{margin:5px 0}
	.rmcg b.k{font-weight:750}
	.rmcg .note{margin:12px 0 4px 36px;padding:10px 14px;border-left:3px solid #0F766E;
		background:var(--bg-light-gray,#f5f7f9);border-radius:0 8px 8px 0;font-size:13px}
	.rmcg .note.warn{border-left-color:#B45309}
	.rmcg .note.rule{border-left-color:#DC2626}
	.rmcg table{border-collapse:collapse;margin:10px 0 6px 36px;width:calc(100% - 36px);font-size:13px}
	.rmcg th{text-align:left;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;
		color:var(--text-muted,#6c7680);padding:5px 7px;
		border-bottom:1px solid var(--border-color,#e2e6ea)}
	.rmcg td{padding:5px 7px;border-bottom:1px solid var(--border-color,#f0f2f4);vertical-align:top}
	.rmcg .btns{margin:12px 0 2px 36px;display:flex;gap:8px;flex-wrap:wrap}
	.rmcg .flow{margin:10px 0 6px 36px;font-family:ui-monospace,Consolas,monospace;
		font-size:12.5px;background:var(--bg-light-gray,#f5f7f9);border-radius:8px;
		padding:12px 14px;white-space:pre;overflow-x:auto}
	.rmcg .up{position:fixed;right:26px;bottom:26px;z-index:5}
</style>
`);
	page.set_primary_action(__('Management view'), () => frappe.set_route('rmc-manage'));
	page.add_menu_item(__('Control Tower'), () => frappe.set_route('rmc-control-tower'));
	page.add_menu_item(__('Report hub'), () => frappe.set_route('rmc-reports'));
};

# RMC Plant Smart ERP — User Guide

**MIDHUNATECH** · Monitor · Manage · Produce · Deliver

This guide follows the plant's own day: set up once, then material in, concrete
out, truck back, bill raised.

---

## 1. Who does what

| Role | Works in | Day-to-day |
|---|---|---|
| **RMC Manager** | every workspace | orders, rates, MIS, approvals |
| **Plant Operator** | RMC Production, RMC Materials | batching, consumption, plant status |
| **Dispatch Incharge** | RMC Dispatch | truck allocation, challans, cycle time |
| **Quality Engineer** | RMC Quality | cube tests, slump, mix designs |
| **RMC Accounts** | RMC Dispatch, RMC Materials | invoices, supplier bills |

## 2. One-time setup (RMC Setup workspace)

1. **RMC Plant** — plant name, capacity m³/hr, raw-material and finished-concrete warehouses.
2. **Concrete Grade** — M10 to M60 ship pre-loaded with strength, application and rate. Each grade automatically has a sellable item (`RMC-M25`, etc.).
3. **Mix Design** — the per-m³ recipe for each grade: cement, fly ash, sand, 20 mm, 10 mm, admixture, water. The app checks the batched weight lands in the normal 1800–2800 kg/m³ band and computes the water/cement ratio and material cost per m³ for you.
4. **Silo** — one record per silo, yard or tank, each pointing at its own warehouse. **The warehouse balance is the silo level** — no separate stock register.
5. **Transit Mixer** — vehicle number, capacity m³, ownership, default driver, fitness and insurance validity.
6. **Construction Site** — customer, address, distance from plant (drives cycle time and freight).
7. **RMC Settings** — default plant, and the two automation switches: *auto Sales Invoice on challan* and *auto Stock Entry on batch*.

## 3. Raw material in — Material Inward

**RMC Materials → Material Inward → New**

- Pick the supplier, the item and the **silo** it is unloaded into (that sets the warehouse).
- Enter **gross** and **tare** weight from the weighbridge; net is calculated.
- Enter rate; amount is calculated.
- Untick *Quality Accepted* to record a rejection — a rejected load cannot be submitted into stock.

On submit the app raises a **Purchase Receipt**, so the stock lands in the silo
and the supplier liability is booked. The silo level updates instantly.

*Watch:* **Silo and Stock Status** report — any silo at or below its low level
shows `LOW - REORDER`.

## 4. Order from the customer — Concrete Order

**RMC Dispatch → Concrete Order → New**

- Customer, construction site, grade, quantity in m³, rate, required dates.
- Add the **pour schedule** rows (date, time slot, quantity) for a staged pour.
- Tick *Concrete Pump Required* if a pump must be sent.

Guard rails: the site must belong to the customer, the schedule cannot exceed
the order, and a customer whose **RMC Credit Status** is *Hold* cannot be given
a new order at all.

Delivered and pending quantities are **never typed** — they are recomputed from
the challans every time one is submitted or cancelled, and the status moves
Open → In Progress → Completed on its own.

## 5. Making the concrete — Batch Production

**RMC Production → Batch Production → New**

1. Date, shift, plant, grade and mix design.
2. Link the **Concrete Order** the pour belongs to (leave blank for stock production).
3. Enter the **produced quantity in m³** — the material grid fills itself from the recipe: target quantity per item.
4. Type the **actual** quantity the plant weighed for each material. Variance % is shown per line, so over- or under-dosing is visible immediately.
5. Save and submit.

On submit the app posts a **Stock Entry (Manufacture)**: every raw material
leaves its own silo warehouse and the finished concrete arrives in the finished
warehouse, valued at the real batch cost per m³.

The mix design must match the grade — the app refuses a mismatch.

*Watch:* **Material Consumption vs Recipe** report — target vs actual vs
variance % by day, grade and item. This is where mix theft and mis-calibrated
load cells show up.

## 6. Sending it out — Delivery Challan

**RMC Dispatch → Delivery Challan → New**

- Pick the order (customer, site, grade and rate fill in), the quantity, the transit mixer and driver, and the batch it was loaded from.
- **Dispatch time** when it leaves; site arrival, unloading end and plant return as the trip proceeds. **Cycle time** is computed from dispatch → return, the core RMC productivity number.
- Record **slump at site** and temperature; tick *Cubes Taken* if the QC engineer sampled the load.
- Set status Dispatched → Delivered → Returned. The truck's own status follows: it becomes *On Trip* on dispatch and *Available* when it returns.

On submit the app raises the **Sales Invoice** (with stock update), so the
concrete leaves the finished warehouse and the revenue is booked in one step.
The challan cannot over-deliver the order — the most common RMC billing
dispute is blocked at source.

**Printing:** the challan prints on the branded *RMC Delivery Challan* format —
customer, site, grade, quantity, vehicle, driver, dispatch and arrival times,
QR code for site-side verification and a signature block. Print, PDF, e-mail or
WhatsApp it.

## 7. Quality — Cube Test

**RMC Quality → Cube Test → New**

- Link the batch; grade and casting date come with it.
- Choose the age (7 / 14 / 28 days) and enter the achieved strength.

Pass or fail is decided for you: IS 456 expects 65 % of the characteristic
strength at 7 days and 100 % at 28. A failed cube raises a red quality alert.

*Watch:* **Cube Test Register** — required vs achieved vs achieved %, with the
result column.

## 8. The plant itself — RMC Quality workspace

- **Plant Status Log** — running / idle / breakdown / stopped blocks with from-to times. A reason is mandatory for breakdown and stopped. This feeds **availability %**.
- **Breakdown Log** — equipment, reported and resolved time (downtime computed), reason, action taken, repair cost. A transit-mixer breakdown puts that vehicle *Under Maintenance* automatically.
- **RMC Maintenance Task** — the preventive schedule; rows flip to *Due* and *Overdue* by themselves each night.
- **Power Log** — EB units and hours, DG units and hours, diesel litres and cost.

## 9. Live dashboard

**RMC Plant Ops → RMC Live Dashboard** (`/app/rmc-live-dashboard`)

One screen for the plant office wall: current plant status and power source,
today's produced m³, dispatched m³, trips and dispatch value, availability %,
running and breakdown hours, every silo's level with a low-stock bar, and the
pending order book. It refreshes itself every two minutes.

## 10. Reports

| Report | Answers |
|---|---|
| Daily Production Summary | how much of each grade, per shift, at what cost per m³ |
| Batch Register | every batch with its order, customer, operator and stock entry |
| Material Consumption vs Recipe | actual vs theoretical consumption and variance |
| Production Target vs Actual | ordered vs delivered vs pending per order |
| Material Inward Register | every weighbridge ticket with supplier and value |
| Silo and Stock Status | live level, filled %, low-stock alert, stock value |
| Dispatch Register | every challan with vehicle, driver, cycle time, slump, invoice |
| Customer Order Status | per customer: orders, ordered, delivered, pending, value |
| Vehicle Utilisation and Trips | trips, m³, average load, average cycle time, revenue carried |
| Customer Wise Sales | value by customer and grade |
| Cube Test Register | required vs achieved strength, pass/fail |
| Plant Availability and Downtime | running, idle, breakdown hours and availability % per day |
| Power and Diesel Consumption | EB and DG units, diesel litres and litres per kWh |
| Breakdown and Maintenance Log | every stoppage with downtime and repair cost |

## 11. Everyday rules the app enforces

- A challan can never deliver more than its order has left.
- A batch's mix design must be for the batch's grade.
- Gross weight must exceed tare; net is always gross − tare.
- Material that failed quality cannot be taken into stock.
- A customer on credit hold cannot be given a new order.
- Breakdown and stopped plant time need a written reason.
- A cancelled order must have its challans cancelled first.
- Cancelling a batch or challan cancels the stock entry or invoice with it.

## 12. Month-end

1. **Customer Order Status** — chase anything still Open or In Progress.
2. **Material Consumption vs Recipe** — investigate any item beyond ±2 % variance.
3. **Silo and Stock Status** — reconcile silo levels with the physical dip.
4. **Plant Availability and Downtime** — availability against the target set in RMC Settings.
5. **Customer Wise Sales** vs ERPNext's Accounts Receivable — they are the same invoices, so they must agree.

---

*MIDHUNATECH — Monitor · Manage · Optimize · Grow*

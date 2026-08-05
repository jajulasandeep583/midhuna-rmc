# RMC Plant Management

Ready Mix Concrete plant ERP for Frappe / ERPNext v16, by **MIDHUNATECH**.

Monitor · Manage · Produce · Deliver — from raw material inward to the signed
delivery challan, in one app that sits on top of standard ERPNext stock and
accounting rather than beside it.

---

## What it does

| Area | What you get |
|---|---|
| **Production** | Mix designs per grade (M10–M60), batch production with target-vs-actual consumption, automatic Manufacture stock entry, cube tests with IS-456 pass/fail |
| **Raw material** | Weighbridge inward (gross/tare/net), automatic Purchase Receipt, silo-wise stock where the warehouse balance *is* the silo level, low-level alerts |
| **Inventory** | Every silo and yard is a warehouse, so ERPNext's stock ledger, valuation and reports work unchanged |
| **Dispatch** | Customer orders with pour schedules, truck allocation, delivery challan with QR + signature, cycle-time tracking, automatic Sales Invoice |
| **Customers** | Customer master, construction sites with distance, order book, credit hold |
| **Plant ops** | Running / idle / breakdown clock, availability %, breakdown log, maintenance schedule, EB + DG power and diesel log |
| **Reports** | 14 query reports covering production, batches, consumption vs recipe, inward, silo stock, dispatch, vehicles, customers, quality, availability, power |
| **Desk** | 6 role-scoped workspaces, 12 number cards, 9 charts, a live plant dashboard page |

Everything is code-first: the whole product rebuilds from this repository with
`bench install-app rmc` — no manual desk configuration.

## Install

```bash
bench get-app rmc <repo-url>
bench new-site rmc.local --install-app erpnext
bench --site rmc.local install-app rmc
```

`after_install` creates the roles, company, items, warehouses, silos, grades,
mix designs, custom fields, print format and workspaces.

The DocTypes themselves are generated once from `rmc/setup/build_doctypes.py`
(developer mode) and are then plain files in the app:

```bash
bench --site rmc.local execute rmc.setup.build_doctypes.build
```

## Demo data

One month of realistic operations — orders, batches, challans, inwards, cube
tests, plant status, breakdowns and power logs, all posted through the real
document chain:

```bash
bench --site rmc.local execute rmc.setup.demo.build     # add
bench --site rmc.local execute rmc.setup.demo.reset     # wipe transactions, keep masters
```

## Audit

An end-to-end self-test — schema, masters, the document chain, ledger
reconciliation, derived values, every report, every workspace, and the guard
rails (over-delivery, wrong mix design, credit hold):

```bash
bench --site rmc.local execute rmc.setup.audit.run
```

## The document chain

```
Material Inward ──submit──▶ Purchase Receipt ──▶ stock into the silo warehouse
                                                 │
Concrete Order ─────────────────────────────┐    │
                                            ▼    ▼
                       Batch Production ──submit──▶ Stock Entry (Manufacture)
                                            │        raw material out, concrete in
                                            ▼
                       Delivery Challan ──submit──▶ Sales Invoice (update stock)
                                            │        concrete out, revenue booked
                                            ▼
                       Concrete Order delivered / pending recomputed
```

Nothing is double-entered: delivered quantity, pending quantity, order status,
cycle time, batch cost, cube-test result and silo level are all derived.

## Modules

- **RMC Setup** — plant, concrete grades, mix designs, transit mixers, construction sites, silos, settings
- **RMC Materials** — material inward
- **RMC Production** — batch production, batch materials, cube tests
- **RMC Dispatch** — concrete orders, order schedule, delivery challans
- **RMC Plant Ops** — plant status log, breakdown log, maintenance tasks, power log, live dashboard

## Licence

MIT · Midhuna Tech

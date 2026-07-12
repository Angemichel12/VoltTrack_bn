# VoltTrack Backend — Integration Guide

Reference for integrating a frontend (or another service) with the VoltTrack API. Interactive docs are also live at `/api/docs/` (Swagger) and `/api/redoc/` (ReDoc); this file covers the workflow rules that aren't obvious from the schema alone.

## Base setup

- Base path: `/api/`
- Auth: JWT (SimpleJWT). Send `Authorization: Bearer <access>` on every request except register/login/refresh.
- Access token lifetime: 24h. Refresh token lifetime: 7 days, rotated on refresh.
- All responses use the same envelope:

```json
// success
{ "success": true, "message": "...", "data": { ... } }

// error
{ "success": false, "message": "...", "errors": { ... } }
```

`errors` mirrors DRF's field-error shape when validation fails (e.g. `{"phone_number": ["This field is required."]}`).

## Roles

- **admin** — manages users, stations, cars, chargers; sees system-wide reports.
- **staff** — works shifts, runs charging sessions. Self-registers via `/api/auth/register/` (always created as `staff`); admins can also create any role via `/api/admin/users/`.
- **manager** — role exists (`User.role` choice) but has no dedicated endpoints yet; not wired into any workflow.

## Core workflow rules (enforced server-side, not just UI conventions)

1. **Station is chosen per shift, not fixed to a staff account.** There is no `station` field on the user. A staff member picks the station when opening a shift (`POST /api/chargers/shifts/open/`), and that shift's station is what scopes chargers/dashboard/session endpoints for the rest of that shift.
2. **One open shift at a time, globally** — a staff member can't open a second shift (at any station) while one is already open. Attempting it returns an error.
3. **No charging session without an open shift.** `POST /api/sessions/start/` fails with `"You must open a shift before starting a session."` if the staff has none open.
4. **No logout with an open shift.** `POST /api/auth/logout/` returns `"End your shift before logging out."` (400) until the staff closes their shift.
5. **Pricing**: a session's `total_price = watt_consumed × price_per_watt`, where `price_per_watt` is the car's `unique_price` if the admin set one, otherwise the station's `price_per_watt`.
6. **Shift financials are computed, not entered** — `total_kwatt`, `total_earned_money_on_shift`, `total_kwatt_used_on_shift`, `total_car_charged` are all derived from the shift's linked charging sessions when the shift is closed. `money_on_momo` and `end_kwatts_in_cashpower` are the two exceptions: both are entered by the staff member at close time (the latter is the actual CashPower meter reading, deliberately not computed, since real usage can drift from the sum of recorded sessions).
7. **Every charger has a `left` and a `right` port (`Charger.PORTS`), each charges one car independently.** A charger can run up to 2 simultaneous sessions, one per port. Starting a session requires picking a free `port` (`"left"` or `"right"`); starting on an already-occupied port fails with `"Port <left/right> on this charger is already in use."` (also enforced at the DB level via a unique constraint, so it's race-safe). Every place chargers are listed (`GET /api/chargers/`, `GET /api/stations/chargers/`) includes a `ports` array per charger so the UI can show which port is free before the staff picks one.

## Typical staff session flow

```
1. POST /api/auth/login/                          → get access + refresh
2. POST /api/chargers/shifts/open/                 → { station, start_kwatts_in_cashpower } → shift opened
3. (optional) PATCH /api/chargers/shifts/{id}/add-cashpower/  → top up mid-shift
4. POST /api/sessions/register-car/                → register car if new (or GET /api/sessions/search-car/ if returning)
5. POST /api/sessions/start/                       → { charger_id, port, plate_number, starting_car_percentage }
6. POST /api/sessions/end/                         → { session_id, watt_consumed, ending_car_percentage }
   ... repeat 4-6 for more cars during the shift ...
7. PATCH /api/chargers/shifts/{id}/close/           → { money_on_momo, notes? } → totals computed
8. POST /api/auth/logout/                          → { refresh } → now allowed
```

## Endpoint reference

### Auth — `/api/auth/` (no auth required except logout)

| Method | Path | Body | Notes |
|---|---|---|---|
| POST | `register/` | `name, phone_number, password` | Always creates role=`staff`. Returns user + tokens. |
| POST | `login/` | `phone_number, password` | Returns user + `access`/`refresh`. |
| POST | `refresh/` | `refresh` | Returns new `access`/`refresh`. |
| POST | `logout/` | `refresh` | **Auth required.** Blacklists the refresh token. Blocked (400) if staff has an open shift. |

### Admin — `/api/admin/` (IsAdmin only)

Standard DRF router CRUD (`list/retrieve/create/update/partial_update/destroy`) for each:

| Resource | Base path | Notable fields |
|---|---|---|
| Users | `users/` | Create: `name, phone_number, password, role`. No `station` — staff pick it per shift. |
| Stations | `stations/` | `name, price_per_watt`. Also `GET stations/reports/` — system-wide earnings/usage across all stations. |

Cars moved out of this router — see `/api/cars/` below, shared with staff.

### Expenses — `/api/expenses/` (IsAdmin only)

Standard DRF router CRUD for per-station expense records.

| Method | Path | Body | Notes |
|---|---|---|---|
| GET | `` | — | List expenses. Query params: `station`, `date_from`, `date_to` (`YYYY-MM-DD`, inclusive). |
| POST | `` | `station, description, amount_vat_exclusive, input_vat` | `date` is set automatically (auto-now), never sent by the client. |
| GET | `<pk>/` | — | Retrieve one expense. |
| PATCH | `<pk>/` | any of the create fields | Partial update. |
| DELETE | `<pk>/` | — | Delete an expense. |

`Expense` fields returned: `id, station, station_name, description, amount_vat_exclusive, input_vat, date`.

Also exposed as a filterable report under `/api/reports/expenses/` (see Reports below) with the same `station`/`date_from`/`date_to` filters, plus `.xlsx`/`.pdf` twins.

### Stations — `/api/stations/`

| Method | Path | Role | Notes |
|---|---|---|---|
| GET | `` | any authenticated user | List stations — staff need this to pick a station when opening a shift. |
| POST | `` | admin | Create a station. |
| PATCH/DELETE | `<pk>/` | admin | Update/delete a station. |
| POST | `<pk>/set-price/` | admin | Body: `{ "price_per_watt": ... }`. |
| GET | `reports/` | admin | System-wide report (earnings, watt used, sessions) — overall and per-station. |
| GET | `dashboard/` | staff | Summary for the staff's **current open shift** (404 if none open): station, charger count, open shift data, session totals for that shift. |
| GET | `chargers/` | staff | Chargers at the staff's **current open-shift station**. |
| GET | `my-reports/` | staff | Staff's personal history **across all stations they've worked**, not just one — summary, per-charger usage, full shift history. |

### Chargers & Shifts — `/api/chargers/`

| Method | Path | Role | Body / Notes |
|---|---|---|---|
| GET | `` | admin: all / staff: own open-shift station | List chargers — each includes `ports: [{port: "left", available: bool}, {port: "right", available: bool}]`. |
| POST | `` | admin | Create a charger at a station: `{ name, station }`. Always gets a left and a right port, both available. |
| DELETE | `<pk>/` | admin | Delete a charger. |
| POST | `shifts/open/` | staff | `{ station, start_kwatts_in_cashpower, shift_start?, notes? }`. Fails if staff already has an open shift anywhere. |
| PATCH | `shifts/<pk>/add-cashpower/` | staff (own open shift) | `{ amount }` — adds to `addition_kwatt_in_cashpower`. |
| PATCH | `shifts/<pk>/close/` | staff (own open shift) | `{ money_on_momo, end_kwatts_in_cashpower, notes? }` — computes and stores the derived shift totals, records the two staff-entered values, sets `shift_end`. |
| GET | `shifts/history/` | admin: all / staff: own | List shift records. |

`ShiftRecord` fields returned: `station, station_name, staff, staff_name, shift_start, shift_end, start_kwatts_in_cashpower, addition_kwatt_in_cashpower, total_kwatt, total_earned_money_on_shift, total_kwatt_used_on_shift, total_car_charged, money_on_momo, end_kwatts_in_cashpower, notes`.

### Cars — `/api/cars/` (shared: admin + staff, `IsAdminOrStaff`)

Full CRUD, but the response shape and what you're allowed to set depends on role:

| Method | Path | Role | Notes |
|---|---|---|---|
| GET | `` / `<pk>/` | admin or staff | Admin response includes `unique_price`; staff response omits it entirely. |
| POST | `` | admin or staff | Create a car: `plate_number, owner_name?, phone_number?, optional_info?` (+ `unique_price?` for admin only — the field doesn't exist in the staff request/response schema, so staff can't set or see it even by sending it). |
| PATCH | `<pk>/` | admin or staff | Same field restriction as create. |
| DELETE | `<pk>/` | **admin only** | Staff gets 403. |

### Cars (quick lookup) & Sessions — `/api/sessions/` (staff only, `IsAdminOrStaff` for the car endpoints, `IsStaff` for session endpoints)

| Method | Path | Role | Body | Notes |
|---|---|---|---|---|
| POST | `register-car/` | admin or staff | `plate_number, owner_name?, phone_number?, optional_info?` | Get-or-create by plate — convenience wrapper around `/api/cars/` for the shift flow. No `unique_price` here either way. |
| GET | `search-car/?plate=...` | admin or staff | — | **Type-ahead**: `plate` matches anywhere in the plate number (case-insensitive), returns up to 20 matches ordered by plate. Meant to be called on every keystroke so the user can pick the right plate before starting a session; returns `[]` (not 404) when nothing matches yet. |
| POST | `start/` | staff | `charger_id, port ("left"/"right"), plate_number, starting_car_percentage` | Requires an open shift; charger must belong to that shift's station; the chosen `port` must not already have an active session on that charger. |
| POST | `end/` | staff | `session_id, watt_consumed, ending_car_percentage` | Computes `total_price` (car `unique_price` else station `price_per_watt`) and `duration`. |
| GET | `my-sessions/` | staff | — | Staff's own sessions, all stations, newest first. |

`ChargingSession` fields returned: `station, station_name, charger, charger_name, port, staff, shift, car, car_plate, starting_car_percentage, ending_car_percentage, watt_consumed, total_price, duration, started_at, ended_at`.

### Reports — `/api/reports/` (`IsAdminOrStaff`; staff always scoped to their own data, admin sees everyone and can filter by staff)

Two report types, each with a JSON endpoint plus Excel/PDF download twins that accept the **same filter query params** and return an attachment:

| Method | Path | Notes |
|---|---|---|
| GET | `sessions/` | JSON: charging sessions report. |
| GET | `sessions/excel/` | Same data as `.xlsx` (`Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`). |
| GET | `sessions/pdf/` | Same data as `.pdf` (landscape table). |
| GET | `shifts/` | JSON: shift report. |
| GET | `shifts/excel/` | Same data as `.xlsx`. |
| GET | `shifts/pdf/` | Same data as `.pdf`. |
| GET | `expenses/` | JSON: station expenses report. **Admin only** (unlike the two reports above). |
| GET | `expenses/excel/` | Same data as `.xlsx`. |
| GET | `expenses/pdf/` | Same data as `.pdf`. |

**Filters (query params, all optional)**:
- `staff` — admin only; staff requests ignore/can't override this, always scoped to themselves. Invalid (non-integer) values return a 400 with a clear message, not a 500. Not applicable to the expenses report (no staff field).
- `station` — station id.
- `charger` — session report only.
- `shift` — session report only, filter to one shift's sessions.
- `date_from` / `date_to` — `YYYY-MM-DD`, inclusive, filtered on `started_at` (sessions) / `shift_start` (shifts) / `date` (expenses).

**Session report row**: `shift_id, staff_name, station_name, charger_name, port, car_plate, starting_car_percentage, ending_car_percentage, watt_consumed, duration, total_price, started_at, ended_at`. `total_price` ("paid") is the same auto-calculated value from the session itself — never entered directly.

**Shift report row**: `staff_name, station_name, shift_start, start_kwatts_in_cashpower, addition_kwatt_in_cashpower, total_kwatt, total_earned_money_on_shift, total_kwatt_used_on_shift, money_on_momo, end_kwatts_in_cashpower, shift_end, total_car_charged`.

**Expenses report row**: `id, station_name, description, amount_vat_exclusive, input_vat, date`.

### Dashboard — `/api/dashboard/` (`IsAdminOrStaff`; staff always scoped to their own sessions/shifts, admin sees everyone)

Aggregated, chart-ready JSON for a stats dashboard — no HTML/rendering, just numbers for a frontend to plot. Same `station` / `date_from` / `date_to` filters as the reports endpoints (staff can't override the implicit scoping to their own data).

| Method | Path | Notes |
|---|---|---|
| GET | `summary/` | KPI tiles: `total_revenue, total_kwatt_used, total_sessions, total_shifts, stations`. Admin responses add `total_expenses, net_revenue` (staff can't see expenses at all, per the admin-only `Expense` resource). |
| GET | `revenue-trend/` | Line-chart data: `[{date, revenue}, ...]` grouped by day. Admin entries also carry `expenses` for days with recorded expenses. |
| GET | `station-usage/` | Bar-chart data: `[{station_id, station_name, sessions, kwatt_used, revenue}, ...]` — one row per station the user has sessions at. |
| GET | `shift-activity/` | `[{date, shifts, earnings, kwatt_used, cars_charged}, ...]` grouped by day, from the same derived `ShiftRecord` totals used in the shift report. |

`total_expenses` in `summary/` is `amount_vat_exclusive + input_vat` summed across matching expenses (i.e. total cash outlay including VAT), not just the VAT-exclusive amount.

## Models quick-reference

- **User**: `name, phone_number (login id), role (admin/manager/staff), is_active`. No station.
- **Station**: `name, price_per_watt`.
- **Charger**: `name, station`. Fixed `left`/`right` ports (`Charger.PORTS`); availability is derived, not stored.
- **ShiftRecord**: see fields above — one open shift per staff member at a time, station chosen at open-time. `money_on_momo` and `end_kwatts_in_cashpower` are staff-entered at close; everything else derived is computed.
- **Car**: `plate_number (unique), owner_name, phone_number, unique_price (admin-only), optional_info`.
- **ChargingSession**: linked to `station, charger, port, staff, shift, car`; `total_price` and `duration` are computed, not sent by the client. DB-level unique constraint prevents two active sessions on the same charger+port.
- **Expense**: `station, description, amount_vat_exclusive, input_vat`, all entered by an admin; `date` is auto-set on creation and not sent by the client. Admin-only resource.

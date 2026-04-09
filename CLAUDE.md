# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PerPetsStore ERP — full-stack accounting + inventory + sales system for a pet store. Vue 3 SPA frontend, Django REST API backend, PostgreSQL.

## Commands

### Frontend (`/frontend`)
```bash
npm run dev       # Dev server at localhost:5173
npm run build     # vue-tsc + vite build (must pass before commits)
```

### Backend (`/backend`)
```bash
# Activate venv: PowerShell `venv\Scripts\Activate.ps1`, bash `source venv/Scripts/activate`
python manage.py runserver              # localhost:8000
python manage.py makemigrations api     # after model changes
python manage.py migrate
python manage.py test api               # backend tests
```

## Architecture

### Stack
- **Frontend**: Vue 3 (Composition API `<script setup>`), TypeScript, Vite, Pinia, Vue Router, Tailwind, ECharts, Axios, jsPDF, xlsx
- **Backend**: Django + Django REST Framework, JWT auth via SimpleJWT, django-filters, openpyxl
- **DB**: PostgreSQL (creds in repo-root `.env`); SQLite fallback in dev

### Backend (`backend/api/`)
Single Django app. Key modules:

- **`models.py`** — Core entities:
  - Accounting: `AccountSubject`, `JournalVoucher` (has `is_posted`), `JournalVoucherItem`
  - Catalog: `Product`, `ProductPackaging`, `Category` (2-level, self-FK parent), `Supplier`, `Customer`
  - Operations: `PurchaseOrder`, `PurchaseApplyItem`, `InventoryBatch`, `Order`, `OrderItem`
- **`services.py`** — All multi-step business logic lives here, NOT in views:
  - `deduct_inventory_fifo()` — FIFO ordered by `created_at, id`
  - `create_inventory_from_purchase()` — multiplies `qty * packaging.quantity` to base units; updates weighted-average `Product.last_cost`
  - `complete_order()` — FIFO deduct in base units + auto-creates two `is_posted=True` vouchers (revenue + COGS)
- **`xlsx_parser.py`** — Multi-section sheet parser for bulk product import. Supports `?sheet=` to pick a worksheet.
- **`views.py`** — DRF `ModelViewSet`s + dashboard `APIView`s. `ProductViewSet` exposes custom actions `bulk-import` and `parse-xlsx`.
- **`serializers.py`** — `ProductSerializer.packagings` is nested writable; uses in-place reconcile preserving FK refs (FK-referenced rows are protected from delete).
- **`urls.py`** — Router under `/api/`.

### Frontend (`frontend/src/`)
- **`api/client.ts`** — Axios with JWT bearer interceptor (token in `localStorage`); response interceptor handles 401 (refresh) / 403 / 500.
- **`api/*.ts`** — Per-domain modules. `inventory.ts` includes `bulkImportProducts` + `parseProductsXlsx`.
- **`views/*.vue`** — One per route. `InventoryView.vue` is the largest (~2k lines, 4 tabs: 商品/水位/盤點/採購).
- **`style.css`** — Contains a global mobile responsive layer (`@media (max-width: 767px)`) that collapses arbitrary-value grids, sticky modals, scrollable tab nav, etc. Touch targets ≥40px.

## Critical Business Rules

1. **`PurchaseApplyItem.fee` semantics**: per-PACKAGING unit price (NOT line total). `line_total = fee * quantity`. Inventory base units = `quantity * packaging.quantity`. Frontend, backend, PDF export all share this convention — don't reintroduce the old "fee = line total" assumption.
2. **FIFO ordering**: `deduct_inventory_fifo()` orders by `created_at` then `id`. Never change.
3. **Double-entry**: Debit total must equal credit total. Enforced in both forms and serializer.
4. **Auto-journal on `complete_order()`**: Creates 2 vouchers (revenue + COGS) with `is_posted=True`. Don't duplicate this in views.
5. **`is_posted` filter on reports**: Dashboard aggregations and 試算/損益/資產負債表 must filter `voucher__is_posted=True`. Manual vouchers default to unposted; users explicitly tick "已入帳" (default checked in the create modal).
6. **Decimal places**: Prices and costs (`Product.current_price/last_cost`, `ProductPackaging.price/cost`, `PurchaseApplyItem.fee`, `InventoryBatch.unit_cost`, `OrderItem.selling_price`) use **3 decimal places**. Journal voucher amounts and order totals use **2 decimal places** (money totals).
7. **Packaging FK fallback**: `OrderItem.packaging` and `PurchaseApplyItem.packaging` are nullable `SET_NULL`. Services resolve effective packaging via `item.packaging or product.packagings.filter(is_default=True).first() or product.packagings.filter(quantity=1).first()`.
8. **Category depth**: Max 2 levels (top + child). `Category.clean()` enforces this. Deletes are PROTECT'd if any Product references the category.
9. **Voucher numbers**: System-generated vouchers use timestamped unique numbers for audit trail — never reuse.
10. **Auth**: JWT access + refresh tokens; refresh interceptor in `api/client.ts`.

## Configuration

- **`.env`** (repo root) — `SECRET_KEY`, `DEBUG`, `DB_*`
- **`tsconfig.json`** — alias `@` → `./src`
- CORS allowed: `localhost:5173`, `127.0.0.1:5173`

## System Specification

`PerPetsStore_ERP_系統規格書.txt` (repo root) is the authoritative spec — UI constraints (warm color scheme, no cyberpunk), accounting rules, FIFO logic, dashboard requirements. Read before significant architectural changes.

## Working in this repo

- The user prefers background agents for non-trivial implementation work — main thread stays free for conversation.
- Auto-commit + push after each completed task. No need to ask.
- Respect existing migration history (currently up to `0012_*`); generate new migrations rather than editing old ones.

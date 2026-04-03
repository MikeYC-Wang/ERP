# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PerPetsStore ERP — a full-stack accounting and e-commerce management system for a pet store. Combines a Vue 3 SPA frontend with a Django REST API backend.

## Commands

### Frontend (`/frontend`)
```bash
npm run dev       # Dev server at localhost:5173
npm run build     # TypeScript compile + Vite build
npm run preview   # Preview production build
```

### Backend (`/backend`)
```bash
# Activate venv first: source /c/Code/SideProject/ERP/venv/Scripts/activate
python manage.py runserver              # Dev server at localhost:8000
python manage.py migrate                # Apply migrations
python manage.py makemigrations api     # Generate migrations after model changes
python manage.py createsuperuser        # Create admin user
python manage.py test api               # Run backend tests
```

## Architecture

### Stack
- **Frontend**: Vue 3 (Composition API `<script setup>`), TypeScript, Vite, Pinia, Vue Router, TailwindCSS, ECharts, Axios
- **Backend**: Python/Django 6, Django REST Framework, django-cors-headers, django-filters
- **Database**: PostgreSQL (primary); falls back to SQLite3 in dev (`backend/db.sqlite3`)

### Backend (`backend/api/`)
Single Django app with all business logic:

- **`models.py`** — 9 models: `AccountSubject`, `JournalVoucher`, `JournalVoucherItem`, `Product`, `PurchaseOrder`, `PurchaseApplyItem`, `InventoryBatch`, `Order`, `OrderItem`
- **`services.py`** — Core business logic. All complex operations go here, not in views:
  - `deduct_inventory_fifo()` — FIFO inventory deduction ordered by `created_at` + `id`
  - `create_inventory_from_purchase()` — Creates `InventoryBatch` records when purchase is received
  - `complete_order()` — Deducts FIFO inventory + auto-generates 2 journal vouchers (COGS and revenue entries)
- **`views.py`** — DRF ViewSets for 9 resources + 4 `APIView` dashboard endpoints
- **`serializers.py`** — DRF serializers
- **`urls.py`** — Router-based REST routes under `/api/` + dashboard endpoints

### Frontend (`frontend/src/`)
- **`router/index.ts`** — 5 routes: `/dashboard`, `/accounting`, `/inventory`, `/orders`, `/settings`
- **`api/client.ts`** — Axios instance; request interceptor auto-attaches Bearer token from `localStorage`; response interceptor handles 401/403/500
- **`api/*.ts`** — One module per domain: `accounting.ts`, `inventory.ts`, `orders.ts`, `dashboard.ts`
- **`stores/theme.ts`** — Pinia store for dark/light mode
- **`layouts/MainLayout.vue`** — Shell layout: collapsible sidebar + header + `<router-view>`
- **`views/*.vue`** — Full-featured page components (~6–45 KB each); one per route

## Critical Business Rules

1. **Amount source**: Purchase amounts must come from `PurchaseApplyItem.fee`, not from the parent `PurchaseOrder` total.
2. **FIFO inventory**: `deduct_inventory_fifo()` orders batches strictly by `created_at`, then `id`. Do not change this ordering.
3. **Double-entry accounting**: Debit total must equal credit total. Enforced in both frontend forms and backend validation.
4. **Auto-journal entries**: When an order is completed (`complete_order()`), two system-generated vouchers are created automatically — do not duplicate this logic in views.
5. **Order metric scoping**: Revenue/cost calculations in the Orders view only count items in the currently active status tab.
6. **Voucher numbers**: System-generated vouchers use timestamped unique numbers for audit trail — do not reuse or reassign.

## Configuration

- **`.env`** (repo root) — `SECRET_KEY`, `DEBUG`, and DB credentials (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`)
- **`tsconfig.json`** — Path alias `@` → `./src`
- CORS whitelist: `localhost:5173` and `127.0.0.1:5173`
- Auth: Bearer token stored in `localStorage` (attached by Axios interceptor)

## System Specification

`PerPetsStore_ERP_系統規格書.txt` (repo root) is the authoritative spec document. It contains UI/UX constraints (warm color scheme, no cyberpunk aesthetics), detailed accounting rules, FIFO logic, and dashboard chart requirements. Read it before making significant architectural or UI changes.

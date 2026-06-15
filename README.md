# Nexova AI

Custom Frappe app for ERPNext v15.90.1 / Frappe v15.90.0.

This repository contains source files only. It does not modify ERPNext core, Docker files, or any existing ERPNext setup.

## MVP Features

- Desk page: **Nexova AI**
- Chat UI inside Frappe Desk
- Browser voice input using the Web Speech API when supported
- Text-to-speech replies using the browser Speech Synthesis API
- Whitelisted backend method: `nexova_ai.api.ask_ai(question)`
- Secure MVP ERPNext queries using `frappe.get_list` only:
  - Today's submitted sales invoices
  - Stock balance from `Bin`
  - Pending receivables from submitted sales invoices

## Later Docker Installation Steps

Run these later from your ERPNext Docker/bench environment, not from this source creation step.

```bash
bench get-app /path/to/nexova_ai
bench --site your-site.local install-app nexova_ai
bench --site your-site.local migrate
bench --site your-site.local clear-cache
bench restart
```

If the app is mounted into an existing container instead of fetched with `bench get-app`, make sure the app folder is available on the bench Python path before running:

```bash
bench --site your-site.local install-app nexova_ai
```

## Usage

After installation, open Desk and search for **Nexova AI**.

Example questions:

- `today's sales`
- `stock balance`
- `stock balance for ITEM-001`
- `pending receivables`

## Notes

The MVP intentionally avoids raw SQL and uses only `frappe.get_list`, so normal Frappe permissions are respected.

# Nexova AI

Custom Frappe app for ERPNext. The current VM deployment is pinned to ERPNext/Frappe v15; v16 compatibility should be validated on a separate test branch and VM before upgrading production-like sites.

This repository contains source files only. It does not modify ERPNext core, Docker files, or any existing ERPNext setup.

## Production V1 Foundation

- Workspace: **Nexova AI**
- Desk page: **Nexova AI Assistant**
- Chat UI inside Frappe Desk
- Browser voice input using the Web Speech API when supported
- Text-to-speech replies using the browser Speech Synthesis API
- Whitelisted backend method: `nexova_ai.api.ask_ai(question)`
- Secure ERPNext queries using `frappe.get_list` only:
  - Today's submitted sales invoices
  - Stock balance from `Bin`
  - Pending receivables from submitted sales invoices
- Production foundations:
  - Single DocType: **Nexova AI Settings**
  - Audit DocType: **Nexova AI Audit Log**
  - Settings-based enable/disable, required role, subscription status, and audit toggles
  - Non-blocking audit logging for assistant requests
  - Workspace shortcuts for assistant, settings, and audit log

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

After installation, open:

- Workspace: `/app/nexova-ai`
- Assistant: `/app/nexova-ai-assistant`

Example questions:

- `today's sales`
- `stock balance`
- `stock balance for ITEM-001`
- `pending receivables`
- `unpaid invoices`
- `outstanding receivables`

## Notes

The assistant intentionally avoids raw SQL and uses only `frappe.get_list`, so normal Frappe permissions are respected.

Voice recognition is provided by the user's browser through the Web Speech API. Nexova AI normalizes common speech-to-text variants before matching supported intents, but the browser still controls the raw transcript quality.

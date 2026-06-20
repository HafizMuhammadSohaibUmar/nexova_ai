# Invoxia AI Custom App Standards

Invoxia AI is an ERPNext add-on app. It must remain isolated from ERPNext and Frappe core.

## Boundaries

- Do not modify ERPNext core files.
- Do not modify Frappe core files.
- Do not monkey patch core classes, modules, or Desk internals.
- Put all UI, APIs, DocTypes, patches, fixtures, and assets inside `nexova_ai`.
- Deploy by rebuilding the custom Docker image from the GitHub app source.

## Current Supported Surface

- Workspace route: `/app/nexova-ai`
- Assistant Desk Page route: `/app/nexova-ai-assistant`
- Standard Page export path:
  - `nexova_ai/nexova_ai/page/nexova_ai_assistant/`
- Workspace export path:
  - `nexova_ai/nexova_ai/workspace/nexova_ai/`
- Backend API namespace:
  - `nexova_ai.api`

## Desk Page Rules

- Use Frappe standard Page exports for Desk pages.
- Do not use `app_include_js` to preload Page controllers.
- Do not use `page_js` unless a specific Frappe-supported use case requires it.
- Keep Workspace route and Page route distinct to avoid route resolution conflicts.

## Future DocTypes

Add DocTypes only when the feature needs persistent data. Planned DocTypes:

- `Nexova AI Settings`
- `Nexova AI Conversation`
- `Nexova AI Message`
- `Nexova AI Action Log`
- `Nexova AI Knowledge Source`
- `Nexova AI Subscription`

## Patches And Fixtures

- Add patches only for schema/data migrations that must run on installed sites.
- Add fixtures only for controlled records that must ship with the app.
- Avoid exporting ad hoc site state as fixtures.

## Tests

At minimum, keep structure tests for:

- Standard Page export paths.
- Workspace shortcut route.
- Hook hygiene.
- JSON validity.

Add Frappe integration tests when adding permission-aware APIs, DocTypes, and write operations.

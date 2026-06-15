# Intent Schema

## Purpose

Mistral is used to classify user intent, extract parameters, and help format responses. The intent output must be structured JSON so the backend can validate it before any ERP tool is executed.

The backend must treat Mistral output as untrusted. Only validated intents from a local allowlist may trigger Python ERP tools.

## Intent Output JSON Schema

```json
{
  "type": "object",
  "required": [
    "intent",
    "confidence",
    "parameters",
    "required_confirmation",
    "risk_level",
    "user_message"
  ],
  "additionalProperties": false,
  "properties": {
    "intent": {
      "type": "string",
      "description": "Canonical intent name selected from the backend allowlist."
    },
    "confidence": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Model confidence in the intent classification."
    },
    "parameters": {
      "type": "object",
      "description": "Extracted parameters needed by the selected tool. Values must be validated by the backend."
    },
    "required_confirmation": {
      "type": "boolean",
      "description": "True if the request is sensitive, broad, or action-oriented and needs explicit user confirmation."
    },
    "risk_level": {
      "type": "string",
      "enum": ["low", "medium", "high", "blocked"],
      "description": "Risk level of the user's request."
    },
    "user_message": {
      "type": "string",
      "description": "Short message to show when clarification, confirmation, or refusal is needed."
    }
  }
}
```

## Canonical Intent Groups

### Supported Read Intents

- `sales_summary`
- `purchase_summary`
- `stock_balance_summary`
- `receivables_summary`
- `payables_summary`
- `customer_summary`
- `supplier_summary`
- `item_lookup`
- `quotation_summary`
- `sales_order_summary`
- `purchase_order_summary`
- `invoice_summary`
- `profit_loss_summary`
- `cash_flow_summary`
- `hr_summary`
- `project_summary`
- `support_ticket_summary`

### Control Intents

- `needs_clarification`
- `unsupported`
- `unsafe_bulk_request`
- `permission_sensitive_request`
- `future_action_request`

## Required Backend Validation

Before executing any ERP tool, the backend must validate:

- `intent` is in the local allowlist.
- `confidence` is above the configured threshold.
- `risk_level` is not `blocked`.
- `parameters` match the expected tool schema.
- Dates are valid and bounded.
- Company, customer, supplier, item, warehouse, and project values are permission-aware.
- The user has required Frappe permissions.
- The request is not asking for a bulk export.

If validation fails, no ERP tool should run.

## Risk Levels

### `low`

Read-only, narrow, normal business summary.

Examples:

- Today's sales total
- Stock balance for one item
- Pending receivables total

### `medium`

Read-only but sensitive, financial, HR-related, or broad enough to need careful limits.

Examples:

- Profit and loss for this quarter
- HR attendance summary
- Cash flow for a company

### `high`

Potential future write action, sensitive operational change, or request needing explicit confirmation.

Examples:

- Draft a sales order
- Create a support ticket
- Prepare a purchase order

### `blocked`

Unsafe, unsupported, or non-compliant request.

Examples:

- Export all invoices
- Show all employee salaries
- Dump all customers
- Query arbitrary database tables
- Ignore permissions

## Example Intent Output

```json
{
  "intent": "stock_balance_summary",
  "confidence": 0.92,
  "parameters": {
    "item_code": "ITEM-001",
    "warehouse": null,
    "company": null
  },
  "required_confirmation": false,
  "risk_level": "low",
  "user_message": ""
}
```

## Example Unsafe Bulk Request

```json
{
  "intent": "unsafe_bulk_request",
  "confidence": 0.95,
  "parameters": {
    "requested_data": "all invoices"
  },
  "required_confirmation": false,
  "risk_level": "blocked",
  "user_message": "I cannot export all invoices through chat. Please narrow the request by date, company, customer, or status."
}
```

## Parameter Extraction Rules

Mistral may extract:

- Date ranges
- Company names
- Customer names
- Supplier names
- Item codes
- Warehouse names
- Document statuses
- Summary type
- Currency references

Mistral must not invent:

- Document names
- Company names
- Customer names
- Item codes
- Amounts
- Permissions
- Tool names outside the allowlist

## Response Formatting Role

After the backend executes a tool, Mistral may format the final response using only:

- Original user question
- Accepted intent
- Validated parameters
- Compact tool output
- Backend safety instructions

Mistral must not add values that are not present in the tool output.

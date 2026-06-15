# ERP Tool Registry

## Purpose

This document defines the planned ERP tool registry for `nexova_ai`. Tools are explicit Python functions that fetch or summarize ERPNext data through permission-aware Frappe APIs.

Mistral may classify intent and extract parameters, but it must never query ERPNext directly. The orchestration layer chooses a registered tool only after validating the Mistral intent output.

## Tool Design Rules

Every tool must define:

- Tool name
- Purpose
- Required role or permission
- Input parameters
- Output schema
- Safety notes

Every tool must:

- Respect Frappe user permissions.
- Apply tenant and company scoping.
- Use explicit doctypes and fields.
- Return compact summaries instead of bulk records.
- Enforce row limits.
- Reject broad or unsafe requests.
- Avoid raw SQL unless separately reviewed and approved.
- Log execution metadata.

## Common Output Envelope

All tools should return a consistent envelope:

```json
{
  "tool": "tool_name",
  "status": "success | empty | denied | needs_clarification | error",
  "summary": "Short human-readable summary",
  "data": {},
  "meta": {
    "tenant": "site-or-tenant-id",
    "company": "company-or-null",
    "currency": "currency-or-null",
    "row_count": 0,
    "truncated": false
  }
}
```

The `data` object must be specific to each tool and must not contain unrestricted record dumps.

## Sales Tools

### `sales_summary`

Purpose: Summarize submitted sales over a bounded date range.

Required role/permission:

- Read permission on `Sales Invoice`
- Company access for the requested company

Input parameters:

- `from_date`: required date
- `to_date`: required date
- `company`: optional string
- `currency`: optional string
- `group_by`: optional enum, one of `day`, `company`, `currency`

Output schema:

```json
{
  "total_sales_by_currency": {"PKR": 0.0},
  "invoice_count": 0,
  "from_date": "YYYY-MM-DD",
  "to_date": "YYYY-MM-DD",
  "grouped_totals": []
}
```

Safety notes:

- Default date range should be today if not provided.
- Long date ranges should return aggregated totals only.
- Do not return full invoice rows.

## Purchase Tools

### `purchase_summary`

Purpose: Summarize submitted purchases over a bounded date range.

Required role/permission:

- Read permission on `Purchase Invoice`
- Company access for the requested company

Input parameters:

- `from_date`: required date
- `to_date`: required date
- `company`: optional string
- `supplier`: optional string
- `group_by`: optional enum, one of `day`, `supplier`, `company`, `currency`

Output schema:

```json
{
  "total_purchases_by_currency": {"PKR": 0.0},
  "purchase_invoice_count": 0,
  "from_date": "YYYY-MM-DD",
  "to_date": "YYYY-MM-DD",
  "grouped_totals": []
}
```

Safety notes:

- Supplier filters must be exact or selected from permission-aware lookup.
- Do not expose line-item details unless a future narrow tool is approved.

## Stock Tools

### `stock_balance_summary`

Purpose: Summarize stock balance from `Bin`.

Required role/permission:

- Read permission on `Bin`
- Read permission on `Item` if item metadata is included
- Warehouse access where configured

Input parameters:

- `item_code`: optional string
- `warehouse`: optional string
- `company`: optional string if warehouse-company mapping is used

Output schema:

```json
{
  "item_code": "ITEM-001",
  "warehouse": "Stores - NX",
  "total_actual_qty": 0.0,
  "bin_count": 0,
  "top_warehouses": []
}
```

Safety notes:

- Without an item filter, return aggregate totals only.
- Limit warehouse breakdown rows.
- Do not return full item master data.

## Receivables Tools

### `receivables_summary`

Purpose: Summarize outstanding customer receivables.

Required role/permission:

- Read permission on `Sales Invoice`
- Company access for the requested company

Input parameters:

- `company`: optional string
- `customer`: optional string
- `as_of_date`: optional date
- `aging_bucket`: optional enum, one of `all`, `current`, `30`, `60`, `90_plus`

Output schema:

```json
{
  "total_outstanding_by_currency": {"PKR": 0.0},
  "invoice_count": 0,
  "aging": {
    "current": 0.0,
    "30": 0.0,
    "60": 0.0,
    "90_plus": 0.0
  }
}
```

Safety notes:

- Customer-level detail requires customer filter or a limited top-N summary.
- Do not return all unpaid invoices.

## Payables Tools

### `payables_summary`

Purpose: Summarize outstanding supplier payables.

Required role/permission:

- Read permission on `Purchase Invoice`
- Company access for the requested company

Input parameters:

- `company`: optional string
- `supplier`: optional string
- `as_of_date`: optional date
- `aging_bucket`: optional enum, one of `all`, `current`, `30`, `60`, `90_plus`

Output schema:

```json
{
  "total_outstanding_by_currency": {"PKR": 0.0},
  "invoice_count": 0,
  "aging": {
    "current": 0.0,
    "30": 0.0,
    "60": 0.0,
    "90_plus": 0.0
  }
}
```

Safety notes:

- Supplier-level detail requires supplier filter or a limited top-N summary.
- Do not return all unpaid purchase invoices.

## Customer Tools

### `customer_summary`

Purpose: Provide a compact summary for a specific customer.

Required role/permission:

- Read permission on `Customer`
- Read permission on related sales documents only if included

Input parameters:

- `customer`: required string
- `company`: optional string
- `include_balances`: optional boolean
- `include_recent_activity`: optional boolean

Output schema:

```json
{
  "customer": "Customer Name",
  "status": "active-or-disabled",
  "outstanding_by_currency": {"PKR": 0.0},
  "recent_sales_count": 0,
  "recent_sales_total_by_currency": {"PKR": 0.0}
}
```

Safety notes:

- Require an exact customer identifier or a permission-aware disambiguation flow.
- Avoid exposing contact details unless explicitly approved.

## Supplier Tools

### `supplier_summary`

Purpose: Provide a compact summary for a specific supplier.

Required role/permission:

- Read permission on `Supplier`
- Read permission on related purchase documents only if included

Input parameters:

- `supplier`: required string
- `company`: optional string
- `include_balances`: optional boolean
- `include_recent_activity`: optional boolean

Output schema:

```json
{
  "supplier": "Supplier Name",
  "status": "active-or-disabled",
  "outstanding_by_currency": {"PKR": 0.0},
  "recent_purchase_count": 0,
  "recent_purchase_total_by_currency": {"PKR": 0.0}
}
```

Safety notes:

- Require an exact supplier identifier or disambiguation.
- Avoid exposing bank or tax details.

## Item Tools

### `item_lookup`

Purpose: Return a safe item summary.

Required role/permission:

- Read permission on `Item`
- Read permission on `Bin` if stock is included

Input parameters:

- `item_code`: required string
- `include_stock`: optional boolean
- `warehouse`: optional string

Output schema:

```json
{
  "item_code": "ITEM-001",
  "item_name": "Item Name",
  "disabled": false,
  "stock_uom": "Nos",
  "total_actual_qty": 0.0
}
```

Safety notes:

- Do not return valuation rates, buying rates, or pricing unless a specific pricing tool is approved.

## Quotation Tools

### `quotation_summary`

Purpose: Summarize quotations by status, customer, and date range.

Required role/permission:

- Read permission on `Quotation`

Input parameters:

- `from_date`: optional date
- `to_date`: optional date
- `customer`: optional string
- `status`: optional string
- `company`: optional string

Output schema:

```json
{
  "quotation_count": 0,
  "total_by_currency": {"PKR": 0.0},
  "status_breakdown": []
}
```

Safety notes:

- Return totals and counts, not full quotation contents.
- Details for one quotation require a future narrow detail tool.

## Sales Order Tools

### `sales_order_summary`

Purpose: Summarize sales orders by status, delivery date, customer, or company.

Required role/permission:

- Read permission on `Sales Order`

Input parameters:

- `from_date`: optional date
- `to_date`: optional date
- `customer`: optional string
- `status`: optional string
- `company`: optional string

Output schema:

```json
{
  "sales_order_count": 0,
  "total_by_currency": {"PKR": 0.0},
  "status_breakdown": [],
  "overdue_count": 0
}
```

Safety notes:

- Avoid returning item-level order details in broad summaries.

## Purchase Order Tools

### `purchase_order_summary`

Purpose: Summarize purchase orders by status, schedule date, supplier, or company.

Required role/permission:

- Read permission on `Purchase Order`

Input parameters:

- `from_date`: optional date
- `to_date`: optional date
- `supplier`: optional string
- `status`: optional string
- `company`: optional string

Output schema:

```json
{
  "purchase_order_count": 0,
  "total_by_currency": {"PKR": 0.0},
  "status_breakdown": [],
  "overdue_count": 0
}
```

Safety notes:

- Avoid full supplier order books unless filtered and limited.

## Invoice Tools

### `invoice_summary`

Purpose: Summarize sales or purchase invoices by type, status, date range, and party.

Required role/permission:

- Read permission on `Sales Invoice` for sales invoices
- Read permission on `Purchase Invoice` for purchase invoices

Input parameters:

- `invoice_type`: required enum, one of `sales`, `purchase`
- `from_date`: optional date
- `to_date`: optional date
- `party`: optional string
- `status`: optional string
- `company`: optional string

Output schema:

```json
{
  "invoice_type": "sales",
  "invoice_count": 0,
  "total_by_currency": {"PKR": 0.0},
  "outstanding_by_currency": {"PKR": 0.0},
  "status_breakdown": []
}
```

Safety notes:

- Broad invoice requests return summary only.
- Single-invoice detail requires exact invoice name and matching permission.

## Profit and Loss Tools

### `profit_loss_summary`

Purpose: Provide a high-level profit and loss summary over a period.

Required role/permission:

- Appropriate Accounts role
- Read permission on relevant accounting reports or GL data
- Company access

Input parameters:

- `from_date`: required date
- `to_date`: required date
- `company`: required string
- `cost_center`: optional string

Output schema:

```json
{
  "income": 0.0,
  "expense": 0.0,
  "net_profit": 0.0,
  "currency": "PKR",
  "period": {
    "from_date": "YYYY-MM-DD",
    "to_date": "YYYY-MM-DD"
  }
}
```

Safety notes:

- Financial statements are sensitive.
- Require strict role checks.
- Prefer using ERPNext report APIs if available.
- Do not send account-level ledgers to Mistral.

## Cash Flow Tools

### `cash_flow_summary`

Purpose: Provide high-level cash inflow, outflow, and net movement.

Required role/permission:

- Appropriate Accounts role
- Read permission on Payment Entry, Journal Entry, or relevant report data
- Company access

Input parameters:

- `from_date`: required date
- `to_date`: required date
- `company`: required string
- `account`: optional string

Output schema:

```json
{
  "cash_inflow": 0.0,
  "cash_outflow": 0.0,
  "net_cash_flow": 0.0,
  "currency": "PKR"
}
```

Safety notes:

- Return aggregates only.
- Do not expose bank account details broadly.

## HR Tools

### `hr_summary`

Purpose: Provide a safe HR summary such as employee counts, attendance counts, or leave summary.

Required role/permission:

- HR Manager, HR User, or equivalent configured role
- Read permission on relevant HR doctypes

Input parameters:

- `company`: optional string
- `summary_type`: required enum, one of `employee_count`, `attendance`, `leave`
- `from_date`: optional date
- `to_date`: optional date
- `department`: optional string

Output schema:

```json
{
  "summary_type": "employee_count",
  "employee_count": 0,
  "department_breakdown": [],
  "period": {}
}
```

Safety notes:

- HR data is sensitive.
- Do not send employee personal data to Mistral.
- Return counts and aggregates by default.

## Project Tools

### `project_summary`

Purpose: Summarize projects, tasks, progress, and overdue work.

Required role/permission:

- Read permission on `Project`
- Read permission on `Task` if task data is included

Input parameters:

- `project`: optional string
- `company`: optional string
- `status`: optional string
- `include_tasks`: optional boolean

Output schema:

```json
{
  "project_count": 0,
  "status_breakdown": [],
  "overdue_task_count": 0,
  "open_task_count": 0,
  "completed_task_count": 0
}
```

Safety notes:

- Task descriptions may contain sensitive information.
- Broad project summaries should use counts and statuses only.

## Support Ticket Tools

### `support_ticket_summary`

Purpose: Summarize support issues by status, priority, customer, or date range.

Required role/permission:

- Read permission on `Issue`
- Customer or portal user constraints where applicable

Input parameters:

- `from_date`: optional date
- `to_date`: optional date
- `customer`: optional string
- `status`: optional string
- `priority`: optional string

Output schema:

```json
{
  "ticket_count": 0,
  "status_breakdown": [],
  "priority_breakdown": [],
  "overdue_count": 0
}
```

Safety notes:

- Ticket descriptions can include confidential details.
- Return summaries by default.
- Exact ticket detail requires a narrow permission-aware tool.

## Future Action Tools

Write-capable tools are out of scope for MVP and v1. Future action tools should be separate from read tools and require explicit confirmation.

Potential future actions:

- Draft quotation
- Draft sales order
- Draft purchase order
- Draft invoice
- Create support ticket
- Create project task

Future action tools must never submit, cancel, amend, or delete documents without a dedicated approval design.

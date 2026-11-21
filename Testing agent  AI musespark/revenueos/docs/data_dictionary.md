# Data dictionary

All data is synthetic. Primary keys are source ids from the connector, not database sequences, so re-loading updates rows and never duplicates them. Indexes exist on every foreign key and on the date columns used for filtering.

## Core tables

| Table | Purpose | Key columns |
|---|---|---|
| `teams` | Regional sales teams | `name`, `region` |
| `users` | People who log in | `email`, `role` (cro, sales_manager, csm, revops, admin), `team_id` (null means all teams), `password_hash` |
| `accounts` | One row per customer | `domain`, `industry`, `region`, `segment`, `owner_id`, `arr`, `status` (active, churned), `churned_at`, `health_score`, `health_status` |
| `contacts` | People at customers | `account_id`, `title`, `is_executive`, `is_champion`, `last_seen` |
| `deals` | Opportunities | `account_id`, `owner_id`, `amount`, `stage`, `created_at`, `close_date`, `closed_at`, `outcome` (won, lost, null if open), `discount_pct`, `source`, `type` (new, renewal, expansion) |
| `deal_stage_history` | When a deal entered each stage | `deal_id`, `stage`, `entered_at` |
| `activities` | Emails, meetings, calls | `deal_id`, `contact_id`, `type`, `direction`, `occurred_at`, `summary_text` |
| `subscriptions` | Contract terms | `account_id`, `start`, `end`, `mrr`, `seats`, `status` (active, renewed, churned, cancelled), `renewal_date` |
| `invoices` | Billing | `account_id`, `amount`, `issued_date`, `due_date`, `paid_date`, `status` (paid, overdue, open) |
| `payments` | Payments received | `invoice_id`, `account_id`, `amount`, `due_date`, `paid_date`, `status` (on_time, late) |
| `usage_daily` | Product use, one row per account per day | `active_users`, `key_feature_events`, `seats_purchased` |
| `tickets` | Support tickets | `account_id`, `opened_at`, `resolved_at`, `severity` (1 is worst), `subject`, `body_text` |
| `embeddings` | Search index over tickets and activities | `source_table`, `source_id`, `account_id`, `text`, `vector` (512 dimensions) |
| `predictions` | Model scores | `entity_type` (deal, account), `entity_id`, `model_name`, `model_version`, `score`, `reasons_json`, `created_at` |
| `copilot_audit` | Every copilot exchange | `user_id`, `question`, `tools_called_json`, `answer`, `cited_sources_json`, `created_at` |

## Tables added beyond the original spec

| Table or column | Why it was needed |
|---|---|
| `deals.original_close_date`, `deals.close_date_changed_at` | The back-test must know the close date a user saw on a past date. Without these it would use the final date, which leaks the future. |
| `accounts.domain` | Finding duplicate companies whose names differ. |
| `accounts.status`, `accounts.churned_at` | Churn labels and the at-risk list. |
| `subscriptions.seats`, `invoices.issued_date` | Seat utilization, and knowing when an invoice existed. |
| `embeddings.account_id` | Team scoping applies inside vector search. |
| `model_versions` | Which model produced a score, when it was trained, and its measured results. |
| `forecast_snapshots` | Each open deal at the end of each week, which the weekly variance explainer compares. |
| `daily_briefs` | Stored per-user brief, one per day. |
| `data_quality_runs` | Last data-quality result, for the Admin page. |
| `load_rejects` | Rows the loader quarantined, such as orphans, so they stay visible. |

## Citation format

Every record returned to the copilot carries a `cite` value, written as `table#id`. For example, `deals#412`, `accounts#7`, `tickets#55`, `predictions#900`, or `forecast#2026Q4`. `GET /sources/{table}/{id}` resolves a citation, within the user's scope.

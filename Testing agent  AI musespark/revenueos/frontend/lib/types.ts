export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  team_id: number | null;
  team_name: string | null;
}

export interface Reason {
  feature: string;
  value: number;
  impact: number;
  direction: "risk" | "positive";
  text: string;
}

export interface AccountRow {
  id: number;
  name: string;
  domain: string | null;
  industry: string | null;
  region: string;
  segment: string;
  arr: number;
  status: string;
  churned_at: string | null;
  health_score: number | null;
  health_status: string | null;
  owner_name: string | null;
  p_churn: number | null;
  churn_band: string | null;
  cite: string;
}

export interface DealRow {
  id: number;
  name: string;
  account_id: number;
  account_name: string;
  owner_name: string | null;
  team_id: number | null;
  amount: number;
  stage: string;
  type: string;
  created_at: string;
  close_date: string | null;
  closed_at: string | null;
  outcome: string | null;
  discount_pct: number | null;
  p_win: number | null;
  risk_band: string | null;
  value_at_risk: number | null;
  reasons: Reason[];
  cite: string;
}

export interface DealExplain extends DealRow {
  model_version: string | null;
  model_algorithm: string | null;
  prediction_cite: string | null;
}

export interface Account360 {
  account: AccountRow;
  deals: (Omit<DealRow, "account_id" | "account_name" | "owner_name" | "team_id" | "reasons" | "value_at_risk">)[];
  contacts: {
    id: number;
    full_name: string;
    title: string | null;
    is_executive: boolean;
    is_champion: boolean;
    last_seen: string | null;
    cite: string;
  }[];
  subscriptions: {
    id: number;
    start: string;
    end: string | null;
    mrr: number;
    seats: number;
    status: string;
    renewal_date: string | null;
    cite: string;
  }[];
  invoices: {
    id: number;
    amount: number;
    issued_date: string;
    due_date: string;
    paid_date: string | null;
    status: string;
    cite: string;
  }[];
  tickets: {
    id: number;
    opened_at: string;
    resolved_at: string | null;
    severity: number;
    subject: string;
    body_text: string | null;
    cite: string;
  }[];
  usage_trend: { week: string; active_users: number; key_feature_events: number; seats: number }[];
  open_risks: { type: string; text: string; cite: string }[];
  churn_reasons: Reason[];
  timeline: { date: string; kind: string; text: string; cite: string }[];
}

export interface ForecastFigures {
  low: number;
  expected: number;
  high: number;
  closed_won_to_date: number;
  rep_commit: number;
  stage_weighted: number;
  open_deals: number;
  open_pipeline: number;
}

export interface Forecast extends ForecastFigures {
  quarter: string;
  as_of: string;
  simulations: number;
  by_team: (ForecastFigures & { team: string })[];
  by_region: (ForecastFigures & { region: string })[];
  top_deals: {
    id: number;
    name: string;
    amount: number;
    stage: string;
    p_win: number;
    expected_value: number;
    cite: string;
  }[];
  cite: string;
}

export interface ForecastChanges {
  available: boolean;
  quarter?: string;
  previous_date?: string;
  current_date?: string;
  expected_previous?: number;
  expected_current?: number;
  total_change?: number;
  categories: Record<string, { count: number; delta_expected: number }>;
  items: {
    deal_id: number;
    name: string;
    category: string;
    delta_expected: number;
    detail: string;
    cite: string;
  }[];
}

export interface Backtest {
  quarters: {
    quarter: string;
    low: number;
    expected: number;
    high: number;
    stage_weighted: number;
    rep_commit: number;
    actual_from_pipeline: number;
    abs_pct_error_model: number;
    abs_pct_error_stage_weighted: number;
    abs_pct_error_rep_commit: number;
    within_p10_p90: boolean;
  }[];
  mape_model: number;
  mape_stage_weighted: number;
  mape_rep_commit: number;
  p10_p90_coverage: number;
  note: string;
}

export interface RetentionRow {
  account_id: number;
  name: string;
  segment: string;
  region: string;
  owner_name: string | null;
  arr: number;
  p_churn: number;
  band: string | null;
  expected_arr_loss: number;
  renewal_date: string | null;
  reasons: Reason[];
  cite: string;
  prediction_cite: string;
}

export interface RetentionSummary {
  as_of: string;
  scored_accounts: number;
  total_arr: number;
  at_risk_arr: number;
  at_risk_accounts: number;
  watch_arr: number;
  watch_accounts: number;
  expected_arr_loss: number;
  at_risk_account_ids: number[];
}

export interface ExpansionRow {
  account_id: number;
  name: string;
  arr: number;
  seat_utilization: number;
  user_growth: number;
  seats: number;
  triggers: string[];
  cite: string;
}

export interface Brief {
  brief_date: string;
  content: {
    forecast: { quarter: string; low: number; expected: number; high: number; cite: string };
    forecast_change: {
      total_change: number | null;
      categories: Record<string, { count: number; delta_expected: number }>;
      top_items: ForecastChanges["items"];
    };
    top_risks: {
      deal_id: number;
      name: string;
      amount: number;
      p_win: number;
      value_at_risk: number;
      reason: string | null;
      cite: string;
    }[];
    accounts_needing_attention: {
      account_id: number;
      name: string;
      arr: number;
      p_churn: number;
      reason: string | null;
      cite: string;
    }[];
  };
}

export interface ChatResponse {
  answer: string;
  tools_called: { name: string; input: Record<string, unknown>; error: boolean }[];
  citations: string[];
  invalid_citations: string[];
  ungrounded_numbers: string[];
  audit_id: number | null;
  latency_ms: number;
}

export interface AuditRow {
  id: number;
  user_email: string;
  question: string;
  tools_called: { name: string }[];
  answer: string;
  cited_sources: { valid: string[]; invalid: string[]; ungrounded_numbers: string[] };
  created_at: string;
}

export interface ModelRow {
  model_name: string;
  version: string;
  algorithm: string;
  trained_at: string;
  is_active: boolean;
  metrics: {
    selected_algorithm?: string;
    test?: Record<string, { auc: number; auc_ci95: number[]; brier: number; entities: number }>;
    top_decile_capture?: Record<string, { capture_rate: number; captured: number; total_churners: number }>;
  };
}

export interface DataHealth {
  run_at: string | null;
  summary: Record<string, number>;
  load_rejects: number;
  row_counts: Record<string, number>;
}

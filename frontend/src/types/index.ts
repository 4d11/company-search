export interface Company {
  id: number;
  company_name: string;
  company_id: number | null;
  city: string | null;
  description: string | null;
  website_url: string | null;
  employee_count: number | null;
  stage: string | null;
  funding_amount: number | null;
  location: string | null;
  industries: string[];
  target_markets: string[];
  explanation: string | null;
}

export interface FilterOptions {
  locations: string[];
  industries: string[];
  target_markets: string[];
  stages: string[];
  business_models: string[];
  revenue_models: string[];
}

export type OperatorType = "EQ" | "NEQ" | "GT" | "GTE" | "LT" | "LTE";
export type FilterType = "text" | "numeric";
export type LogicType = "AND" | "OR";

export interface FilterRule {
  op: OperatorType;
  value: string | number;
}

export interface SegmentFilter {
  segment: string;
  type: FilterType;
  logic: LogicType;
  rules: FilterRule[];
}

export interface QueryFilters {
  logic: LogicType;
  filters: SegmentFilter[];
}

export interface ExcludedFilterValue {
  segment: string;
  op: string;
  value: string | number;
}

export interface SavedSearch {
  id: string;
  name: string;
  query: string;
  timestamp: number;
  filters: {
    locations: string[];
    industries: string[];
    targetMarkets: string[];
    stages: string[];
    businessModels: string[];
    revenueModels: string[];
    minEmployees: number | null;
    maxEmployees: number | null;
    minFunding: number | null;
    maxFunding: number | null;
  };
}

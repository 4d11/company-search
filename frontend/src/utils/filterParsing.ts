/**
 * Utility functions for parsing and handling filter operations
 */

export interface FilterRule {
  op: string;
  value: string | number;
}

export interface SegmentFilter {
  segment: string;
  type: string;
  logic: string;
  rules: FilterRule[];
}

export interface QueryFilters {
  logic: string;
  filters: SegmentFilter[];
}

/**
 * Check if an operator is a "greater than" type (GT or GTE)
 */
export function isGreaterThanOperator(op: string): boolean {
  const upperOp = op.toUpperCase();
  return upperOp === 'GT' || upperOp === 'GTE';
}

/**
 * Check if an operator is a "less than" type (LT or LTE)
 */
export function isLessThanOperator(op: string): boolean {
  const upperOp = op.toUpperCase();
  return upperOp === 'LT' || upperOp === 'LTE';
}

/**
 * Extract minimum value from numeric filter rules
 */
export function extractMinValue(rules: FilterRule[]): number | null {
  const minRule = rules.find(r => isGreaterThanOperator(r.op));
  return minRule ? Number(minRule.value) : null;
}

/**
 * Extract maximum value from numeric filter rules
 */
export function extractMaxValue(rules: FilterRule[]): number | null {
  const maxRule = rules.find(r => isLessThanOperator(r.op));
  return maxRule ? Number(maxRule.value) : null;
}

/**
 * Extract text values from text filter rules (EQ operator)
 */
export function extractTextValues(rules: FilterRule[]): string[] {
  return rules
    .filter(r => r.op === 'EQ')
    .map(r => r.value as string);
}

/**
 * Format funding amount for display (converts to millions with 1 decimal)
 */
export function formatFundingAmount(amount: number): string {
  return `$${(amount / 1000000).toFixed(1)}M`;
}

/**
 * Check if a QueryFilters object has any active filters
 */
export function hasActiveFilters(filters: QueryFilters | null): boolean {
  if (!filters) return false;
  return filters.filters.length > 0;
}

/**
 * Get a specific segment filter by name
 */
export function getSegmentFilter(
  filters: QueryFilters,
  segmentName: string
): SegmentFilter | undefined {
  return filters.filters.find(f => f.segment === segmentName);
}

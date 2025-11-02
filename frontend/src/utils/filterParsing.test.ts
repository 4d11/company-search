import { describe, it, expect } from 'vitest';
import {
  isGreaterThanOperator,
  isLessThanOperator,
  extractMinValue,
  extractMaxValue,
  extractTextValues,
  formatFundingAmount,
  hasActiveFilters,
  getSegmentFilter,
  type FilterRule,
  type QueryFilters,
} from './filterParsing';

describe('filterParsing utilities', () => {
  describe('isGreaterThanOperator', () => {
    it('returns true for GT operator', () => {
      expect(isGreaterThanOperator('GT')).toBe(true);
    });

    it('returns true for GTE operator', () => {
      expect(isGreaterThanOperator('GTE')).toBe(true);
    });

    it('returns true for lowercase gt', () => {
      expect(isGreaterThanOperator('gt')).toBe(true);
    });

    it('returns true for lowercase gte', () => {
      expect(isGreaterThanOperator('gte')).toBe(true);
    });

    it('returns false for LT operator', () => {
      expect(isGreaterThanOperator('LT')).toBe(false);
    });

    it('returns false for EQ operator', () => {
      expect(isGreaterThanOperator('EQ')).toBe(false);
    });
  });

  describe('isLessThanOperator', () => {
    it('returns true for LT operator', () => {
      expect(isLessThanOperator('LT')).toBe(true);
    });

    it('returns true for LTE operator', () => {
      expect(isLessThanOperator('LTE')).toBe(true);
    });

    it('returns true for lowercase lt', () => {
      expect(isLessThanOperator('lt')).toBe(true);
    });

    it('returns true for lowercase lte', () => {
      expect(isLessThanOperator('lte')).toBe(true);
    });

    it('returns false for GT operator', () => {
      expect(isLessThanOperator('GT')).toBe(false);
    });

    it('returns false for EQ operator', () => {
      expect(isLessThanOperator('EQ')).toBe(false);
    });
  });

  describe('extractMinValue', () => {
    it('extracts value from GTE rule', () => {
      const rules: FilterRule[] = [{ op: 'GTE', value: 50 }];
      expect(extractMinValue(rules)).toBe(50);
    });

    it('extracts value from GT rule', () => {
      const rules: FilterRule[] = [{ op: 'GT', value: 100 }];
      expect(extractMinValue(rules)).toBe(100);
    });

    it('returns null when no GT/GTE rules exist', () => {
      const rules: FilterRule[] = [{ op: 'LT', value: 100 }];
      expect(extractMinValue(rules)).toBe(null);
    });

    it('handles empty rules array', () => {
      expect(extractMinValue([])).toBe(null);
    });

    it('handles case-insensitive operators', () => {
      const rules: FilterRule[] = [{ op: 'gte', value: 25 }];
      expect(extractMinValue(rules)).toBe(25);
    });

    it('converts string value to number', () => {
      const rules: FilterRule[] = [{ op: 'GTE', value: '50' }];
      expect(extractMinValue(rules)).toBe(50);
    });
  });

  describe('extractMaxValue', () => {
    it('extracts value from LTE rule', () => {
      const rules: FilterRule[] = [{ op: 'LTE', value: 500 }];
      expect(extractMaxValue(rules)).toBe(500);
    });

    it('extracts value from LT rule', () => {
      const rules: FilterRule[] = [{ op: 'LT', value: 100 }];
      expect(extractMaxValue(rules)).toBe(100);
    });

    it('returns null when no LT/LTE rules exist', () => {
      const rules: FilterRule[] = [{ op: 'GT', value: 50 }];
      expect(extractMaxValue(rules)).toBe(null);
    });

    it('handles empty rules array', () => {
      expect(extractMaxValue([])).toBe(null);
    });

    it('handles case-insensitive operators', () => {
      const rules: FilterRule[] = [{ op: 'lte', value: 1000 }];
      expect(extractMaxValue(rules)).toBe(1000);
    });
  });

  describe('extractTextValues', () => {
    it('extracts values from EQ rules', () => {
      const rules: FilterRule[] = [
        { op: 'EQ', value: 'New York' },
        { op: 'EQ', value: 'San Francisco' },
      ];
      expect(extractTextValues(rules)).toEqual(['New York', 'San Francisco']);
    });

    it('filters out non-EQ rules', () => {
      const rules: FilterRule[] = [
        { op: 'EQ', value: 'New York' },
        { op: 'GT', value: 100 },
        { op: 'EQ', value: 'Boston' },
      ];
      expect(extractTextValues(rules)).toEqual(['New York', 'Boston']);
    });

    it('returns empty array for no EQ rules', () => {
      const rules: FilterRule[] = [
        { op: 'GT', value: 100 },
        { op: 'LT', value: 500 },
      ];
      expect(extractTextValues(rules)).toEqual([]);
    });

    it('handles empty rules array', () => {
      expect(extractTextValues([])).toEqual([]);
    });
  });

  describe('formatFundingAmount', () => {
    it('formats amount in millions with 1 decimal', () => {
      expect(formatFundingAmount(5000000)).toBe('$5.0M');
    });

    it('handles large amounts', () => {
      expect(formatFundingAmount(50000000)).toBe('$50.0M');
    });

    it('handles small amounts', () => {
      expect(formatFundingAmount(1500000)).toBe('$1.5M');
    });

    it('rounds to 1 decimal place', () => {
      expect(formatFundingAmount(1234567)).toBe('$1.2M');
    });

    it('handles zero', () => {
      expect(formatFundingAmount(0)).toBe('$0.0M');
    });
  });

  describe('hasActiveFilters', () => {
    it('returns true when filters exist', () => {
      const filters: QueryFilters = {
        logic: 'AND',
        filters: [
          {
            segment: 'location',
            type: 'text',
            logic: 'OR',
            rules: [{ op: 'EQ', value: 'New York' }],
          },
        ],
      };
      expect(hasActiveFilters(filters)).toBe(true);
    });

    it('returns false when filters array is empty', () => {
      const filters: QueryFilters = {
        logic: 'AND',
        filters: [],
      };
      expect(hasActiveFilters(filters)).toBe(false);
    });

    it('returns false when filters is null', () => {
      expect(hasActiveFilters(null)).toBe(false);
    });

    it('returns true for multiple filters', () => {
      const filters: QueryFilters = {
        logic: 'AND',
        filters: [
          {
            segment: 'location',
            type: 'text',
            logic: 'OR',
            rules: [{ op: 'EQ', value: 'New York' }],
          },
          {
            segment: 'employee_count',
            type: 'numeric',
            logic: 'AND',
            rules: [{ op: 'LT', value: 100 }],
          },
        ],
      };
      expect(hasActiveFilters(filters)).toBe(true);
    });
  });

  describe('getSegmentFilter', () => {
    const filters: QueryFilters = {
      logic: 'AND',
      filters: [
        {
          segment: 'location',
          type: 'text',
          logic: 'OR',
          rules: [{ op: 'EQ', value: 'New York' }],
        },
        {
          segment: 'employee_count',
          type: 'numeric',
          logic: 'AND',
          rules: [{ op: 'LT', value: 100 }],
        },
      ],
    };

    it('returns segment filter when found', () => {
      const segmentFilter = getSegmentFilter(filters, 'location');
      expect(segmentFilter).toBeDefined();
      expect(segmentFilter?.segment).toBe('location');
    });

    it('returns undefined when segment not found', () => {
      const segmentFilter = getSegmentFilter(filters, 'industries');
      expect(segmentFilter).toBeUndefined();
    });

    it('returns correct filter for employee_count', () => {
      const segmentFilter = getSegmentFilter(filters, 'employee_count');
      expect(segmentFilter).toBeDefined();
      expect(segmentFilter?.segment).toBe('employee_count');
      expect(segmentFilter?.type).toBe('numeric');
    });
  });
});

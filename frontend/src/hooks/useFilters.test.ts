import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useFilters } from './useFilters';

describe('useFilters', () => {
  describe('initial state', () => {
    it('should initialize with empty filters', () => {
      const { result } = renderHook(() => useFilters());

      expect(result.current.selectedLocations).toEqual([]);
      expect(result.current.selectedIndustries).toEqual([]);
      expect(result.current.selectedTargetMarkets).toEqual([]);
      expect(result.current.selectedStages).toEqual([]);
      expect(result.current.selectedBusinessModels).toEqual([]);
      expect(result.current.selectedRevenueModels).toEqual([]);
      expect(result.current.minEmployees).toBeNull();
      expect(result.current.maxEmployees).toBeNull();
      expect(result.current.minFunding).toBeNull();
      expect(result.current.maxFunding).toBeNull();
    });

    it('should have hasActiveFilters as false initially', () => {
      const { result } = renderHook(() => useFilters());
      expect(result.current.hasActiveFilters).toBe(false);
    });
  });

  describe('setters', () => {
    it('should update selected locations', () => {
      const { result } = renderHook(() => useFilters());

      act(() => {
        result.current.setSelectedLocations(['New York', 'San Francisco']);
      });

      expect(result.current.selectedLocations).toEqual(['New York', 'San Francisco']);
      expect(result.current.hasActiveFilters).toBe(true);
    });

    it('should update numeric filters', () => {
      const { result } = renderHook(() => useFilters());

      act(() => {
        result.current.setMinEmployees(50);
        result.current.setMaxEmployees(200);
      });

      expect(result.current.minEmployees).toBe(50);
      expect(result.current.maxEmployees).toBe(200);
      expect(result.current.hasActiveFilters).toBe(true);
    });
  });

  describe('buildFilters', () => {
    it('should return null when no filters are set', () => {
      const { result } = renderHook(() => useFilters());
      const filters = result.current.buildFilters();
      expect(filters).toBeNull();
    });

    it('should build location filter correctly', () => {
      const { result } = renderHook(() => useFilters());

      act(() => {
        result.current.setSelectedLocations(['New York', 'Boston']);
      });

      const filters = result.current.buildFilters();
      expect(filters).toEqual({
        logic: 'AND',
        filters: [{
          segment: 'location',
          type: 'text',
          logic: 'OR',
          rules: [
            { op: 'EQ', value: 'New York' },
            { op: 'EQ', value: 'Boston' }
          ]
        }]
      });
    });

    it('should build numeric range filters correctly', () => {
      const { result } = renderHook(() => useFilters());

      act(() => {
        result.current.setMinEmployees(10);
        result.current.setMaxEmployees(100);
      });

      const filters = result.current.buildFilters();
      expect(filters?.filters[0]).toEqual({
        segment: 'employee_count',
        type: 'numeric',
        logic: 'AND',
        rules: [
          { op: 'GTE', value: 10 },
          { op: 'LTE', value: 100 }
        ]
      });
    });

    it('should build multiple filter segments', () => {
      const { result } = renderHook(() => useFilters());

      act(() => {
        result.current.setSelectedLocations(['NYC']);
        result.current.setSelectedIndustries(['Fintech']);
        result.current.setMinEmployees(50);
      });

      const filters = result.current.buildFilters();
      expect(filters?.filters).toHaveLength(3);
      expect(filters?.logic).toBe('AND');
    });
  });

  describe('clearAllFilters', () => {
    it('should reset all filters to initial state', () => {
      const { result } = renderHook(() => useFilters());

      act(() => {
        result.current.setSelectedLocations(['NYC']);
        result.current.setSelectedIndustries(['Tech']);
        result.current.setMinEmployees(10);
        result.current.setMaxFunding(1000000);
      });

      expect(result.current.hasActiveFilters).toBe(true);

      act(() => {
        result.current.clearAllFilters();
      });

      expect(result.current.selectedLocations).toEqual([]);
      expect(result.current.selectedIndustries).toEqual([]);
      expect(result.current.minEmployees).toBeNull();
      expect(result.current.maxFunding).toBeNull();
      expect(result.current.hasActiveFilters).toBe(false);
    });
  });

  describe('removeFilterValue', () => {
    it('should remove a specific location filter', () => {
      const { result } = renderHook(() => useFilters());

      act(() => {
        result.current.setSelectedLocations(['NYC', 'SF', 'Boston']);
      });

      act(() => {
        result.current.removeFilterValue('location', 'EQ', 'SF');
      });

      expect(result.current.selectedLocations).toEqual(['NYC', 'Boston']);
    });

    it('should clear min employees when removing GTE rule', () => {
      const { result } = renderHook(() => useFilters());

      act(() => {
        result.current.setMinEmployees(50);
        result.current.setMaxEmployees(200);
      });

      act(() => {
        result.current.removeFilterValue('employee_count', 'GTE', 50);
      });

      expect(result.current.minEmployees).toBeNull();
      expect(result.current.maxEmployees).toBe(200);
    });

    it('should add value to excluded list', () => {
      const { result } = renderHook(() => useFilters());

      act(() => {
        result.current.setSelectedLocations(['NYC', 'SF']);
      });

      act(() => {
        result.current.removeFilterValue('location', 'EQ', 'NYC');
      });

      expect(result.current.excludedValues).toContainEqual({
        segment: 'location',
        op: 'EQ',
        value: 'NYC'
      });
    });
  });

  describe('hasActiveFilters', () => {
    it('should return true when text filters are set', () => {
      const { result } = renderHook(() => useFilters());

      act(() => {
        result.current.setSelectedIndustries(['Tech']);
      });

      expect(result.current.hasActiveFilters).toBe(true);
    });

    it('should return true when numeric filters are set', () => {
      const { result } = renderHook(() => useFilters());

      act(() => {
        result.current.setMinFunding(100000);
      });

      expect(result.current.hasActiveFilters).toBe(true);
    });

    it('should return false when all filters are empty', () => {
      const { result } = renderHook(() => useFilters());

      act(() => {
        result.current.setSelectedLocations(['NYC']);
      });

      act(() => {
        result.current.clearAllFilters();
      });

      expect(result.current.hasActiveFilters).toBe(false);
    });
  });
});

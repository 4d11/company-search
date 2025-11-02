import { useState, useMemo } from "react";
import { QueryFilters, SegmentFilter, FilterRule, ExcludedFilterValue } from "../types";

export const useFilters = () => {
  const [selectedLocations, setSelectedLocations] = useState<string[]>([]);
  const [selectedIndustries, setSelectedIndustries] = useState<string[]>([]);
  const [selectedTargetMarkets, setSelectedTargetMarkets] = useState<string[]>([]);
  const [selectedStages, setSelectedStages] = useState<string[]>([]);
  const [selectedBusinessModels, setSelectedBusinessModels] = useState<string[]>([]);
  const [selectedRevenueModels, setSelectedRevenueModels] = useState<string[]>([]);
  const [minEmployees, setMinEmployees] = useState<number | null>(null);
  const [maxEmployees, setMaxEmployees] = useState<number | null>(null);
  const [minFunding, setMinFunding] = useState<number | null>(null);
  const [maxFunding, setMaxFunding] = useState<number | null>(null);
  const [appliedFilters, setAppliedFilters] = useState<QueryFilters | null>(null);
  const [excludedValues, setExcludedValues] = useState<ExcludedFilterValue[]>([]);

  const hasActiveFilters = useMemo(
    () =>
      selectedLocations.length > 0 ||
      selectedIndustries.length > 0 ||
      selectedTargetMarkets.length > 0 ||
      selectedStages.length > 0 ||
      selectedBusinessModels.length > 0 ||
      selectedRevenueModels.length > 0 ||
      minEmployees !== null ||
      maxEmployees !== null ||
      minFunding !== null ||
      maxFunding !== null,
    [selectedLocations, selectedIndustries, selectedTargetMarkets, selectedStages, selectedBusinessModels, selectedRevenueModels, minEmployees, maxEmployees, minFunding, maxFunding]
  );

  const buildFilters = (): QueryFilters | null => {
    const segmentFilters: SegmentFilter[] = [];

    if (selectedLocations.length > 0) {
      segmentFilters.push({
        segment: "location",
        type: "text",
        logic: "OR",
        rules: selectedLocations.map((loc) => ({ op: "EQ", value: loc })),
      });
    }

    if (selectedIndustries.length > 0) {
      segmentFilters.push({
        segment: "industries",
        type: "text",
        logic: "OR",
        rules: selectedIndustries.map((ind) => ({ op: "EQ", value: ind })),
      });
    }

    if (selectedTargetMarkets.length > 0) {
      segmentFilters.push({
        segment: "target_markets",
        type: "text",
        logic: "OR",
        rules: selectedTargetMarkets.map((tm) => ({ op: "EQ", value: tm })),
      });
    }

    if (selectedStages.length > 0) {
      segmentFilters.push({
        segment: "funding_stage",
        type: "text",
        logic: "OR",
        rules: selectedStages.map((stage) => ({ op: "EQ", value: stage })),
      });
    }

    if (selectedBusinessModels.length > 0) {
      segmentFilters.push({
        segment: "business_models",
        type: "text",
        logic: "OR",
        rules: selectedBusinessModels.map((model) => ({ op: "EQ", value: model })),
      });
    }

    if (selectedRevenueModels.length > 0) {
      segmentFilters.push({
        segment: "revenue_models",
        type: "text",
        logic: "OR",
        rules: selectedRevenueModels.map((model) => ({ op: "EQ", value: model })),
      });
    }

    if (minEmployees !== null || maxEmployees !== null) {
      const employeeRules: FilterRule[] = [];
      if (minEmployees !== null) employeeRules.push({ op: "GTE", value: minEmployees });
      if (maxEmployees !== null) employeeRules.push({ op: "LTE", value: maxEmployees });
      segmentFilters.push({
        segment: "employee_count",
        type: "numeric",
        logic: "AND",
        rules: employeeRules,
      });
    }

    if (minFunding !== null || maxFunding !== null) {
      const fundingRules: FilterRule[] = [];
      if (minFunding !== null) fundingRules.push({ op: "GTE", value: minFunding });
      if (maxFunding !== null) fundingRules.push({ op: "LTE", value: maxFunding });
      segmentFilters.push({
        segment: "funding_amount",
        type: "numeric",
        logic: "AND",
        rules: fundingRules,
      });
    }

    return segmentFilters.length === 0 ? null : { logic: "AND", filters: segmentFilters };
  };

  const clearAllFilters = () => {
    setSelectedLocations([]);
    setSelectedIndustries([]);
    setSelectedTargetMarkets([]);
    setSelectedStages([]);
    setSelectedBusinessModels([]);
    setSelectedRevenueModels([]);
    setMinEmployees(null);
    setMaxEmployees(null);
    setMinFunding(null);
    setMaxFunding(null);
    setAppliedFilters(null);
    setExcludedValues([]);
  };

  const removeFilterValue = (segment: string, op: string, value: string | number) => {
    const newExcludedValue: ExcludedFilterValue = { segment, op, value };
    setExcludedValues([...excludedValues, newExcludedValue]);

    if (appliedFilters) {
      const updatedFilters = appliedFilters.filters
        .map((segmentFilter) => {
          if (segmentFilter.segment === segment) {
            const remainingRules = segmentFilter.rules.filter(
              (rule) => !(rule.op === op && String(rule.value) === String(value))
            );
            if (remainingRules.length > 0) {
              return { ...segmentFilter, rules: remainingRules };
            }
            return null;
          }
          return segmentFilter;
        })
        .filter((f) => f !== null) as SegmentFilter[];

      setAppliedFilters({ ...appliedFilters, filters: updatedFilters });
    }

    switch (segment) {
      case "location":
        setSelectedLocations((prev) => prev.filter((loc) => loc !== value));
        break;
      case "industries":
        setSelectedIndustries((prev) => prev.filter((ind) => ind !== value));
        break;
      case "target_markets":
        setSelectedTargetMarkets((prev) => prev.filter((tm) => tm !== value));
        break;
      case "funding_stage":
        setSelectedStages((prev) => prev.filter((stage) => stage !== value));
        break;
      case "business_models":
        setSelectedBusinessModels((prev) => prev.filter((bm) => bm !== value));
        break;
      case "revenue_models":
        setSelectedRevenueModels((prev) => prev.filter((rm) => rm !== value));
        break;
      case "employee_count":
        if (op === "GTE" || op === "GT") setMinEmployees(null);
        else if (op === "LTE" || op === "LT") setMaxEmployees(null);
        break;
      case "funding_amount":
        if (op === "GTE" || op === "GT") setMinFunding(null);
        else if (op === "LTE" || op === "LT") setMaxFunding(null);
        break;
    }
  };

  return {
    selectedLocations,
    selectedIndustries,
    selectedTargetMarkets,
    selectedStages,
    selectedBusinessModels,
    selectedRevenueModels,
    minEmployees,
    maxEmployees,
    minFunding,
    maxFunding,
    appliedFilters,
    excludedValues,
    hasActiveFilters,
    setSelectedLocations,
    setSelectedIndustries,
    setSelectedTargetMarkets,
    setSelectedStages,
    setSelectedBusinessModels,
    setSelectedRevenueModels,
    setMinEmployees,
    setMaxEmployees,
    setMinFunding,
    setMaxFunding,
    setAppliedFilters,
    setExcludedValues,
    buildFilters,
    clearAllFilters,
    removeFilterValue,
  };
};

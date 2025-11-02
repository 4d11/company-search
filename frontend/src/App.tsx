import "./App.css";
import { useState, useEffect, useCallback, useMemo } from "react";
import axios from "axios";
import { FilterAutocomplete } from "./components/FilterAutocomplete";
import { NumericRangeFilter } from "./components/NumericRangeFilter";
import { CompanyCard } from "./components/CompanyCard";
import { API_ENDPOINTS, FILTER_CONFIG, NUMERIC_FILTER_CONFIG } from "./constants/filters";

interface Company {
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

interface FilterOptions {
  locations: string[];
  industries: string[];
  target_markets: string[];
  stages: string[];
  business_models: string[];
  revenue_models: string[];
}

type OperatorType = "EQ" | "NEQ" | "GT" | "GTE" | "LT" | "LTE";
type FilterType = "text" | "numeric";
type LogicType = "AND" | "OR";

interface FilterRule {
  op: OperatorType;
  value: string | number;
}

interface SegmentFilter {
  segment: string;
  type: FilterType;
  logic: LogicType;
  rules: FilterRule[];
}

interface QueryFilters {
  logic: LogicType;
  filters: SegmentFilter[];
}

const exampleQueries = [
  "Find Stealth Pre-seed companies",
  "AI B2B SaaS in San Francisco",
  "Find companies with founders who have a prior exit",
  "security ai startups",
  "productivity tool SaaS based in New York"
];

function App() {
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [placeholder, setPlaceholder] = useState("");

  // Filter states
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({
    locations: [],
    industries: [],
    target_markets: [],
    stages: [],
    business_models: [],
    revenue_models: []
  });
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

  // Applied filters from backend and excluded segments
  const [appliedFilters, setAppliedFilters] = useState<QueryFilters | null>(null);
  const [excludedSegments, setExcludedSegments] = useState<string[]>([]);

  const fetchFilterOptions = useCallback(async () => {
    try {
      const response = await axios.get(API_ENDPOINTS.FILTER_OPTIONS);
      setFilterOptions(response.data);
    } catch (err) {
      console.error("Error fetching filter options:", err);
    }
  }, []);

  useEffect(() => {
    // Randomly select a placeholder on component mount
    const randomQuery = exampleQueries[Math.floor(Math.random() * exampleQueries.length)];
    setPlaceholder(`e.g. ${randomQuery}`);

    // Fetch filter options
    fetchFilterOptions();
  }, [fetchFilterOptions]);

  const buildFilters = (): QueryFilters | null => {
    const segmentFilters: SegmentFilter[] = [];

    // Location filter (text, EQ with OR logic for multiple)
    if (selectedLocations.length > 0) {
      segmentFilters.push({
        segment: "location",
        type: "text",
        logic: "OR",
        rules: selectedLocations.map(loc => ({ op: "EQ", value: loc }))
      });
    }

    // Industries filter (text, EQ with OR logic for multiple)
    if (selectedIndustries.length > 0) {
      segmentFilters.push({
        segment: "industries",
        type: "text",
        logic: "OR",
        rules: selectedIndustries.map(ind => ({ op: "EQ", value: ind }))
      });
    }

    // Target Markets filter (text, EQ with OR logic for multiple)
    if (selectedTargetMarkets.length > 0) {
      segmentFilters.push({
        segment: "target_markets",
        type: "text",
        logic: "OR",
        rules: selectedTargetMarkets.map(tm => ({ op: "EQ", value: tm }))
      });
    }

    // Funding Stage filter (text, EQ with OR logic for multiple)
    if (selectedStages.length > 0) {
      segmentFilters.push({
        segment: "funding_stage",
        type: "text",
        logic: "OR",
        rules: selectedStages.map(stage => ({ op: "EQ", value: stage }))
      });
    }

    // Business Models filter (text, EQ with OR logic for multiple)
    if (selectedBusinessModels.length > 0) {
      segmentFilters.push({
        segment: "business_models",
        type: "text",
        logic: "OR",
        rules: selectedBusinessModels.map(model => ({ op: "EQ", value: model }))
      });
    }

    // Revenue Models filter (text, EQ with OR logic for multiple)
    if (selectedRevenueModels.length > 0) {
      segmentFilters.push({
        segment: "revenue_models",
        type: "text",
        logic: "OR",
        rules: selectedRevenueModels.map(model => ({ op: "EQ", value: model }))
      });
    }

    // Employee count filter (numeric, GTE/LTE)
    if (minEmployees !== null || maxEmployees !== null) {
      const employeeRules: FilterRule[] = [];
      if (minEmployees !== null) {
        employeeRules.push({ op: "GTE", value: minEmployees });
      }
      if (maxEmployees !== null) {
        employeeRules.push({ op: "LTE", value: maxEmployees });
      }
      segmentFilters.push({
        segment: "employee_count",
        type: "numeric",
        logic: "AND",
        rules: employeeRules
      });
    }

    // Funding amount filter (numeric, GTE/LTE)
    if (minFunding !== null || maxFunding !== null) {
      const fundingRules: FilterRule[] = [];
      if (minFunding !== null) {
        fundingRules.push({ op: "GTE", value: minFunding });
      }
      if (maxFunding !== null) {
        fundingRules.push({ op: "LTE", value: maxFunding });
      }
      segmentFilters.push({
        segment: "funding_amount",
        type: "numeric",
        logic: "AND",
        rules: fundingRules
      });
    }

    if (segmentFilters.length === 0) {
      return null;
    }

    return {
      logic: "AND",
      filters: segmentFilters
    };
  };

  const parseAppliedFilters = (filters: QueryFilters) => {
    // Parse applied filters from backend and populate UI state
    filters.filters.forEach(segmentFilter => {
      switch (segmentFilter.segment) {
        case "location":
          const locations = segmentFilter.rules
            .filter(r => r.op === "EQ")
            .map(r => r.value as string);
          setSelectedLocations(locations);
          break;
        case "industries":
          const industries = segmentFilter.rules
            .filter(r => r.op === "EQ")
            .map(r => r.value as string);
          setSelectedIndustries(industries);
          break;
        case "target_markets":
          const markets = segmentFilter.rules
            .filter(r => r.op === "EQ")
            .map(r => r.value as string);
          setSelectedTargetMarkets(markets);
          break;
        case "funding_stage":
          const stages = segmentFilter.rules
            .filter(r => r.op === "EQ")
            .map(r => r.value as string);
          setSelectedStages(stages);
          break;
        case "business_models":
          const businessModels = segmentFilter.rules
            .filter(r => r.op === "EQ")
            .map(r => r.value as string);
          setSelectedBusinessModels(businessModels);
          break;
        case "revenue_models":
          const revenueModels = segmentFilter.rules
            .filter(r => r.op === "EQ")
            .map(r => r.value as string);
          setSelectedRevenueModels(revenueModels);
          break;
        case "employee_count":
          const empMinRule = segmentFilter.rules.find(r => r.op === "GTE");
          const empMaxRule = segmentFilter.rules.find(r => r.op === "LTE");
          if (empMinRule) {
            setMinEmployees(Number(empMinRule.value));
          }
          if (empMaxRule) {
            setMaxEmployees(Number(empMaxRule.value));
          }
          break;
        case "funding_amount":
          const fundMinRule = segmentFilter.rules.find(r => r.op === "GTE");
          const fundMaxRule = segmentFilter.rules.find(r => r.op === "LTE");
          if (fundMinRule) {
            setMinFunding(Number(fundMinRule.value));
          }
          if (fundMaxRule) {
            setMaxFunding(Number(fundMaxRule.value));
          }
          break;
      }
    });
  };

  const handleSubmit = async () => {
    // Allow submission with just filters (no query required)
    if (!inputValue.trim() && !hasActiveFilters) return;

    setIsLoading(true);
    setError(null);

    try {
      // Build filters from current UI state
      const filters = buildFilters();

      const response = await axios.post(API_ENDPOINTS.SUBMIT_QUERY, {
        query: inputValue,
        filters: filters,
        excluded_segments: excludedSegments
      });

      setCompanies(response.data.companies);

      // Update applied filters from backend response
      if (response.data.applied_filters) {
        setAppliedFilters(response.data.applied_filters);
        parseAppliedFilters(response.data.applied_filters);
      }

      // Keep the query in the search bar (don't clear it)
    } catch (err) {
      setError("Failed to submit query. Please try again.");
      console.error("Error submitting query:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && (inputValue.trim() || hasActiveFilters)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const hasActiveFilters = useMemo(() =>
    selectedLocations.length > 0 || selectedIndustries.length > 0 || selectedTargetMarkets.length > 0 ||
    selectedStages.length > 0 || selectedBusinessModels.length > 0 || selectedRevenueModels.length > 0 ||
    minEmployees !== null || maxEmployees !== null || minFunding !== null || maxFunding !== null,
    [selectedLocations, selectedIndustries, selectedTargetMarkets, selectedStages, selectedBusinessModels, selectedRevenueModels, minEmployees, maxEmployees, minFunding, maxFunding]
  );

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
    setExcludedSegments([]);
  };

  const removeFilter = (segment: string) => {
    // Add segment to excluded list
    if (!excludedSegments.includes(segment)) {
      setExcludedSegments([...excludedSegments, segment]);
    }

    // Remove from applied filters
    if (appliedFilters) {
      setAppliedFilters({
        ...appliedFilters,
        filters: appliedFilters.filters.filter(f => f.segment !== segment)
      });
    }

    // Clear UI state for this segment
    switch (segment) {
      case "location":
        setSelectedLocations([]);
        break;
      case "industries":
        setSelectedIndustries([]);
        break;
      case "target_markets":
        setSelectedTargetMarkets([]);
        break;
      case "funding_stage":
        setSelectedStages([]);
        break;
      case "business_models":
        setSelectedBusinessModels([]);
        break;
      case "revenue_models":
        setSelectedRevenueModels([]);
        break;
      case "employee_count":
        setMinEmployees(null);
        setMaxEmployees(null);
        break;
      case "funding_amount":
        setMinFunding(null);
        setMaxFunding(null);
        break;
    }
  };

  const showResults = companies.length > 0 || error;
  const hasSearched = showResults || isLoading;

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-gray-50 to-gray-100">
      <div className={`w-full max-w-5xl mx-auto transition-all duration-500 ${hasSearched ? 'pt-8' : 'min-h-screen flex flex-col justify-center'}`}>
        {/* Search Section */}
        <div className={`flex flex-col items-center gap-6 px-6 ${hasSearched ? '' : 'mb-20'}`}>
          {/* Magnifying Glass Icon - Always visible */}
          <div className={`mb-8 ${isLoading ? 'animate-bounce' : ''}`}>
            <svg
              className="w-24 h-24 text-blue-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>

          {/* Search Bar */}
          <div className={`relative ${hasSearched ? 'w-full' : 'w-full max-w-3xl'}`}>
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              className="w-full h-24 px-6 py-4 pr-24 rounded-3xl border-2 border-gray-200 bg-white text-gray-800 text-lg placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              placeholder={placeholder}
            />
            <button
              onClick={handleSubmit}
              disabled={(!inputValue.trim() && !hasActiveFilters) || isLoading}
              className="absolute bottom-4 right-4 px-6 py-2.5 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm font-semibold disabled:from-gray-300 disabled:to-gray-300 disabled:cursor-not-allowed transition-all hover:shadow-lg hover:scale-105 disabled:hover:scale-100"
              aria-label="Submit"
            >
              {isLoading ? "Searching..." : "Search"}
            </button>
          </div>

          {/* Unified Filter Section */}
          <div className={`${hasSearched ? 'w-full' : 'w-full max-w-3xl'}`}>
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Filters</h3>
                {hasActiveFilters && (
                  <button
                    onClick={clearAllFilters}
                    className="text-xs text-blue-600 hover:text-blue-800 font-medium transition-colors"
                  >
                    Clear all
                  </button>
                )}
              </div>

              {/* Text Filters - Grid Layout */}
              <div className="grid grid-cols-3 gap-3 mb-4">
                <FilterAutocomplete
                  value={selectedLocations}
                  onChange={setSelectedLocations}
                  options={filterOptions.locations}
                  label={FILTER_CONFIG.location.label}
                  emoji={FILTER_CONFIG.location.emoji}
                  chipColor={FILTER_CONFIG.location.colors}
                  disabled={isLoading}
                />

                <FilterAutocomplete
                  value={selectedIndustries}
                  onChange={setSelectedIndustries}
                  options={filterOptions.industries}
                  label={FILTER_CONFIG.industries.label}
                  emoji={FILTER_CONFIG.industries.emoji}
                  chipColor={FILTER_CONFIG.industries.colors}
                  disabled={isLoading}
                />

                <FilterAutocomplete
                  value={selectedTargetMarkets}
                  onChange={setSelectedTargetMarkets}
                  options={filterOptions.target_markets}
                  label={FILTER_CONFIG.targetMarkets.label}
                  emoji={FILTER_CONFIG.targetMarkets.emoji}
                  chipColor={FILTER_CONFIG.targetMarkets.colors}
                  disabled={isLoading}
                />

                <FilterAutocomplete
                  value={selectedStages}
                  onChange={setSelectedStages}
                  options={filterOptions.stages}
                  label={FILTER_CONFIG.stages.label}
                  emoji={FILTER_CONFIG.stages.emoji}
                  chipColor={FILTER_CONFIG.stages.colors}
                  disabled={isLoading}
                />

                <FilterAutocomplete
                  value={selectedBusinessModels}
                  onChange={setSelectedBusinessModels}
                  options={filterOptions.business_models}
                  label={FILTER_CONFIG.businessModels.label}
                  emoji={FILTER_CONFIG.businessModels.emoji}
                  chipColor={FILTER_CONFIG.businessModels.colors}
                  disabled={isLoading}
                />

                <FilterAutocomplete
                  value={selectedRevenueModels}
                  onChange={setSelectedRevenueModels}
                  options={filterOptions.revenue_models}
                  label={FILTER_CONFIG.revenueModels.label}
                  emoji={FILTER_CONFIG.revenueModels.emoji}
                  chipColor={FILTER_CONFIG.revenueModels.colors}
                  disabled={isLoading}
                />
              </div>

              {/* Numeric Filters with Min/Max Inputs */}
              <div className="space-y-4 pt-4 border-t border-gray-200">
                <NumericRangeFilter
                  min={minEmployees}
                  max={maxEmployees}
                  onMinChange={setMinEmployees}
                  onMaxChange={setMaxEmployees}
                  {...NUMERIC_FILTER_CONFIG.employee}
                  disabled={isLoading}
                />

                <NumericRangeFilter
                  min={minFunding}
                  max={maxFunding}
                  onMinChange={setMinFunding}
                  onMaxChange={setMaxFunding}
                  {...NUMERIC_FILTER_CONFIG.funding}
                  disabled={isLoading}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Results Section */}
        {hasSearched && (
          <div className="w-full max-w-5xl mx-auto px-6 mt-8">
                {isLoading && (
              <div className="w-full p-8 rounded-3xl bg-white shadow-lg border border-gray-100">
                <div className="flex items-center gap-4">
                  <div className="w-6 h-6 border-3 border-gray-200 border-t-blue-600 rounded-full animate-spin"></div>
                  <div>
                    <p className="text-gray-800 font-medium">Searching companies...</p>
                    <p className="text-sm text-gray-500">This may take a moment</p>
                  </div>
                </div>
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="w-full p-6 rounded-3xl bg-red-50 shadow-lg border border-red-100">
                <p className="text-red-800 font-medium">{error}</p>
              </div>
            )}

            {/* Results */}
            {companies.length > 0 && !isLoading && (
              <div className="w-full space-y-4">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">✨</span>
                  <h2 className="text-xl font-bold text-gray-800">
                    I've evaluated companies for you. Here are the {companies.length} that matter.
                  </h2>
                </div>
                {companies.map((company) => (
                  <CompanyCard key={company.id} company={company} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

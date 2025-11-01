import "./App.css";
import { useState, useEffect } from "react";
import axios from "axios";
import { Autocomplete, TextField, Chip, Typography } from "@mui/material";

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
    stages: []
  });
  const [selectedLocations, setSelectedLocations] = useState<string[]>([]);
  const [selectedIndustries, setSelectedIndustries] = useState<string[]>([]);
  const [selectedTargetMarkets, setSelectedTargetMarkets] = useState<string[]>([]);
  const [selectedStages, setSelectedStages] = useState<string[]>([]);
  const [minEmployees, setMinEmployees] = useState<number | null>(null);
  const [maxEmployees, setMaxEmployees] = useState<number | null>(null);
  const [minFunding, setMinFunding] = useState<number | null>(null);
  const [maxFunding, setMaxFunding] = useState<number | null>(null);

  // Applied filters from backend and excluded segments
  const [appliedFilters, setAppliedFilters] = useState<QueryFilters | null>(null);
  const [excludedSegments, setExcludedSegments] = useState<string[]>([]);

  useEffect(() => {
    // Randomly select a placeholder on component mount
    const randomQuery = exampleQueries[Math.floor(Math.random() * exampleQueries.length)];
    setPlaceholder(`e.g. ${randomQuery}`);

    // Fetch filter options
    fetchFilterOptions();
  }, []);

  const fetchFilterOptions = async () => {
    try {
      const response = await axios.get("http://localhost:8000/api/filter-options");
      setFilterOptions(response.data);
    } catch (err) {
      console.error("Error fetching filter options:", err);
    }
  };

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

      const response = await axios.post("http://localhost:8000/api/submit-query", {
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

  const hasActiveFilters = selectedLocations.length > 0 || selectedIndustries.length > 0 || selectedTargetMarkets.length > 0 ||
    selectedStages.length > 0 || minEmployees !== null || maxEmployees !== null ||
    minFunding !== null || maxFunding !== null;

  const clearAllFilters = () => {
    setSelectedLocations([]);
    setSelectedIndustries([]);
    setSelectedTargetMarkets([]);
    setSelectedStages([]);
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
              <div className="grid grid-cols-2 gap-3 mb-4">
                <Autocomplete
                  multiple
                  value={selectedLocations}
                  onChange={(_, newValue) => setSelectedLocations(newValue)}
                  options={filterOptions.locations}
                  renderInput={(params) => (
                    <TextField {...params} label="📍 Locations" size="small" variant="outlined" />
                  )}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <Chip
                        label={option}
                        size="small"
                        {...getTagProps({ index })}
                        sx={{
                          backgroundColor: '#DBEAFE',
                          color: '#1E40AF',
                          fontWeight: 500,
                          borderRadius: '16px'
                        }}
                      />
                    ))
                  }
                  disabled={isLoading}
                />

                <Autocomplete
                  multiple
                  value={selectedIndustries}
                  onChange={(_, newValue) => setSelectedIndustries(newValue)}
                  options={filterOptions.industries}
                  renderInput={(params) => (
                    <TextField {...params} label="🏢 Industries" size="small" variant="outlined" />
                  )}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <Chip
                        label={option}
                        size="small"
                        {...getTagProps({ index })}
                        sx={{
                          backgroundColor: '#E8EAFF',
                          color: '#4F46E5',
                          fontWeight: 500,
                          borderRadius: '16px'
                        }}
                      />
                    ))
                  }
                  disabled={isLoading}
                />

                <Autocomplete
                  multiple
                  value={selectedTargetMarkets}
                  onChange={(_, newValue) => setSelectedTargetMarkets(newValue)}
                  options={filterOptions.target_markets}
                  renderInput={(params) => (
                    <TextField {...params} label="🎯 Target Markets" size="small" variant="outlined" />
                  )}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <Chip
                        label={option}
                        size="small"
                        {...getTagProps({ index })}
                        sx={{
                          backgroundColor: '#DCFCE7',
                          color: '#15803D',
                          fontWeight: 500,
                          borderRadius: '16px'
                        }}
                      />
                    ))
                  }
                  disabled={isLoading}
                />

                <Autocomplete
                  multiple
                  value={selectedStages}
                  onChange={(_, newValue) => setSelectedStages(newValue)}
                  options={filterOptions.stages}
                  renderInput={(params) => (
                    <TextField {...params} label="🚀 Funding Stage" size="small" variant="outlined" />
                  )}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <Chip
                        label={option}
                        size="small"
                        {...getTagProps({ index })}
                        sx={{
                          backgroundColor: '#FEF3C7',
                          color: '#92400E',
                          fontWeight: 500,
                          borderRadius: '16px'
                        }}
                      />
                    ))
                  }
                  disabled={isLoading}
                />
              </div>

              {/* Numeric Filters with Min/Max Inputs */}
              <div className="space-y-4 pt-4 border-t border-gray-200">
                {/* Employee Count */}
                <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-4 border border-indigo-100">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-lg">👥</span>
                    <Typography variant="body2" className="text-gray-800 font-semibold">
                      Employee Count
                    </Typography>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <TextField
                      type="number"
                      size="small"
                      label="Min"
                      placeholder="e.g. 50"
                      value={minEmployees ?? ''}
                      onChange={(e) => setMinEmployees(e.target.value ? Number(e.target.value) : null)}
                      disabled={isLoading}
                      InputProps={{
                        inputProps: { min: 0 }
                      }}
                      sx={{
                        backgroundColor: 'white',
                        '& .MuiOutlinedInput-root': {
                          '&:hover fieldset': {
                            borderColor: '#6366F1',
                          },
                          '&.Mui-focused fieldset': {
                            borderColor: '#6366F1',
                          }
                        }
                      }}
                    />
                    <TextField
                      type="number"
                      size="small"
                      label="Max"
                      placeholder="e.g. 500"
                      value={maxEmployees ?? ''}
                      onChange={(e) => setMaxEmployees(e.target.value ? Number(e.target.value) : null)}
                      disabled={isLoading}
                      InputProps={{
                        inputProps: { min: 0 }
                      }}
                      sx={{
                        backgroundColor: 'white',
                        '& .MuiOutlinedInput-root': {
                          '&:hover fieldset': {
                            borderColor: '#6366F1',
                          },
                          '&.Mui-focused fieldset': {
                            borderColor: '#6366F1',
                          }
                        }
                      }}
                    />
                  </div>
                </div>

                {/* Funding Amount */}
                <div className="bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl p-4 border border-emerald-100">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-lg">💰</span>
                    <Typography variant="body2" className="text-gray-800 font-semibold">
                      Funding Amount (USD)
                    </Typography>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <TextField
                      type="number"
                      size="small"
                      label="Min ($)"
                      placeholder="e.g. 1000000"
                      value={minFunding ?? ''}
                      onChange={(e) => setMinFunding(e.target.value ? Number(e.target.value) : null)}
                      disabled={isLoading}
                      InputProps={{
                        inputProps: { min: 0 }
                      }}
                      sx={{
                        backgroundColor: 'white',
                        '& .MuiOutlinedInput-root': {
                          '&:hover fieldset': {
                            borderColor: '#10B981',
                          },
                          '&.Mui-focused fieldset': {
                            borderColor: '#10B981',
                          }
                        }
                      }}
                    />
                    <TextField
                      type="number"
                      size="small"
                      label="Max ($)"
                      placeholder="e.g. 10000000"
                      value={maxFunding ?? ''}
                      onChange={(e) => setMaxFunding(e.target.value ? Number(e.target.value) : null)}
                      disabled={isLoading}
                      InputProps={{
                        inputProps: { min: 0 }
                      }}
                      sx={{
                        backgroundColor: 'white',
                        '& .MuiOutlinedInput-root': {
                          '&:hover fieldset': {
                            borderColor: '#10B981',
                          },
                          '&.Mui-focused fieldset': {
                            borderColor: '#10B981',
                          }
                        }
                      }}
                    />
                  </div>
                </div>
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
                  <div
                    key={company.id}
                    className="p-8 rounded-3xl bg-white shadow-lg border border-gray-100 hover:shadow-xl transition-all hover:scale-[1.01]"
                  >
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xl font-bold flex-shrink-0">
                        {company.company_name.charAt(0).toUpperCase()}
                      </div>
                      <div className="flex-1">
                        <h3 className="text-2xl font-bold text-gray-900 mb-3">
                          {company.company_name}
                        </h3>
                        {company.explanation && (
                          <div className="mb-3 p-3 rounded-xl bg-blue-50 border border-blue-100">
                            <p className="text-sm font-semibold text-blue-900 mb-1">✨ Why this company?</p>
                            <p className="text-sm text-blue-800 leading-relaxed">
                              {company.explanation}
                            </p>
                          </div>
                        )}
                        {company.description && (
                          <p className="text-gray-600 mb-4 text-base leading-relaxed">
                            {company.description}
                          </p>
                        )}
                        <div className="flex flex-wrap gap-2.5 items-center">
                          {company.industries && company.industries.length > 0 && (
                            <div className="flex flex-wrap gap-1.5">
                              {company.industries.map((industry, idx) => (
                                <span key={idx} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-purple-50 text-purple-800 text-xs font-medium border border-purple-200">
                                  🏢 {industry}
                                </span>
                              ))}
                            </div>
                          )}
                          {company.target_markets && company.target_markets.length > 0 && (
                            <div className="flex flex-wrap gap-1.5">
                              {company.target_markets.map((market, idx) => (
                                <span key={idx} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-teal-50 text-teal-800 text-xs font-medium border border-teal-200">
                                  🎯 {market}
                                </span>
                              ))}
                            </div>
                          )}
                          {company.stage && (
                            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-yellow-50 text-yellow-800 text-sm font-semibold border border-yellow-200">
                              🚀 {company.stage}
                            </span>
                          )}
                          {company.funding_amount && (
                            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-green-50 text-green-800 text-sm font-semibold border border-green-200">
                              💰 ${(company.funding_amount / 1000000).toFixed(1)}M
                            </span>
                          )}
                          {company.employee_count && (
                            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-indigo-50 text-indigo-800 text-sm font-semibold border border-indigo-200">
                              👥 {company.employee_count} employees
                            </span>
                          )}
                          {(company.location || company.city) && (
                            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-blue-50 text-blue-700 text-sm font-medium border border-blue-200">
                              📍 {company.location || company.city}
                            </span>
                          )}
                          {company.website_url && (
                            <a
                              href={company.website_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gray-100 text-gray-700 text-sm font-medium hover:bg-gray-200 transition-colors border border-gray-200"
                            >
                              🔗 Website
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
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

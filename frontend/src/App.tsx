import "./App.css";
import { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import {
  CompanyCard,
  CompanyListSkeleton,
  EmptyState,
  FilterPanel,
  FilterPills,
  SavedSearchesModal,
  SaveSearchDialog,
} from "./components";
import { API_ENDPOINTS } from "./constants/filters";
import { useFilters } from "./hooks/useFilters";
import { Company, FilterOptions, SavedSearch } from "./types";

const exampleQueries = [
  "Find Stealth Pre-seed companies",
  "AI B2B SaaS in San Francisco",
  "security ai startups",
  "productivity tool SaaS based in New York",
  "an addition to my seed stage fintech portfolio",
];

function App() {
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [placeholder, setPlaceholder] = useState("");
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({
    locations: [],
    industries: [],
    target_markets: [],
    stages: [],
    business_models: [],
    revenue_models: [],
  });
  const [filtersExpanded, setFiltersExpanded] = useState(false);
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>(() => {
    const saved = localStorage.getItem("savedSearches");
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error("Failed to load saved searches:", e);
        return [];
      }
    }
    return [];
  });
  const [showSavedSearches, setShowSavedSearches] = useState(false);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [saveSearchName, setSaveSearchName] = useState("");
  const [hasPerformedSearch, setHasPerformedSearch] = useState(false);

  const filters = useFilters();
  const prevInputValueRef = useRef<string>("");
  const isInitialMountRef = useRef(true);
  const isLoadingSavedSearchRef = useRef(false);

  const fetchFilterOptions = useCallback(async () => {
    try {
      const response = await axios.get(API_ENDPOINTS.FILTER_OPTIONS);
      setFilterOptions(response.data);
    } catch (err) {
      console.error("Error fetching filter options:", err);
    }
  }, []);

  useEffect(() => {
    const randomQuery = exampleQueries[Math.floor(Math.random() * exampleQueries.length)];
    setPlaceholder(`e.g. ${randomQuery}`);
    fetchFilterOptions();
  }, [fetchFilterOptions]);

  useEffect(() => {
    if (isInitialMountRef.current) {
      isInitialMountRef.current = false;
      prevInputValueRef.current = inputValue;
      return;
    }

    if (isLoadingSavedSearchRef.current) {
      prevInputValueRef.current = inputValue;
      return;
    }

    const prevText = prevInputValueRef.current.trim();
    const currentText = inputValue.trim();
    const shouldClearFilters =
      (currentText === "" && prevText !== "") || (prevText.length > 3 && currentText.length <= 2);

    if (shouldClearFilters) {
      filters.clearAllFilters();
    }

    prevInputValueRef.current = inputValue;
  }, [inputValue, filters]);

  useEffect(() => {
    localStorage.setItem("savedSearches", JSON.stringify(savedSearches));
  }, [savedSearches]);

  const parseAppliedFilters = (queryFilters: any) => {
    queryFilters.filters.forEach((segmentFilter: any) => {
      switch (segmentFilter.segment) {
        case "location":
          filters.setSelectedLocations(segmentFilter.rules.filter((r: any) => r.op === "EQ").map((r: any) => r.value));
          break;
        case "industries":
          filters.setSelectedIndustries(segmentFilter.rules.filter((r: any) => r.op === "EQ").map((r: any) => r.value));
          break;
        case "target_markets":
          filters.setSelectedTargetMarkets(segmentFilter.rules.filter((r: any) => r.op === "EQ").map((r: any) => r.value));
          break;
        case "funding_stage":
          filters.setSelectedStages(segmentFilter.rules.filter((r: any) => r.op === "EQ").map((r: any) => r.value));
          break;
        case "business_models":
          filters.setSelectedBusinessModels(segmentFilter.rules.filter((r: any) => r.op === "EQ").map((r: any) => r.value));
          break;
        case "revenue_models":
          filters.setSelectedRevenueModels(segmentFilter.rules.filter((r: any) => r.op === "EQ").map((r: any) => r.value));
          break;
        case "employee_count":
          const empMinRule = segmentFilter.rules.find((r: any) => r.op.toUpperCase() === "GTE" || r.op.toUpperCase() === "GT");
          const empMaxRule = segmentFilter.rules.find((r: any) => r.op.toUpperCase() === "LTE" || r.op.toUpperCase() === "LT");
          if (empMinRule) filters.setMinEmployees(Number(empMinRule.value));
          if (empMaxRule) filters.setMaxEmployees(Number(empMaxRule.value));
          break;
        case "funding_amount":
          const fundMinRule = segmentFilter.rules.find((r: any) => r.op.toUpperCase() === "GTE" || r.op.toUpperCase() === "GT");
          const fundMaxRule = segmentFilter.rules.find((r: any) => r.op.toUpperCase() === "LTE" || r.op.toUpperCase() === "LT");
          if (fundMinRule) filters.setMinFunding(Number(fundMinRule.value));
          if (fundMaxRule) filters.setMaxFunding(Number(fundMaxRule.value));
          break;
      }
    });
  };

  const handleSubmit = async () => {
    if (!inputValue.trim() && !filters.hasActiveFilters) return;

    setIsLoading(true);
    setError(null);
    setHasPerformedSearch(true);

    try {
      const queryFilters = filters.buildFilters();
      const response = await axios.post(API_ENDPOINTS.SUBMIT_QUERY, {
        query: inputValue,
        filters: queryFilters,
        excluded_values: filters.excludedValues,
      });

      setCompanies(response.data.companies);

      if (response.data.applied_filters) {
        filters.setAppliedFilters(response.data.applied_filters);
        parseAppliedFilters(response.data.applied_filters);
      }
    } catch (err) {
      setError("Failed to submit query. Please try again.");
      console.error("Error submitting query:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement | HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey && (inputValue.trim() || filters.hasActiveFilters)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const saveCurrentSearch = useCallback(() => {
    if (!saveSearchName.trim()) return;

    const newSearch: SavedSearch = {
      id: Date.now().toString(),
      name: saveSearchName.trim(),
      query: inputValue,
      timestamp: Date.now(),
      filters: {
        locations: filters.selectedLocations,
        industries: filters.selectedIndustries,
        targetMarkets: filters.selectedTargetMarkets,
        stages: filters.selectedStages,
        businessModels: filters.selectedBusinessModels,
        revenueModels: filters.selectedRevenueModels,
        minEmployees: filters.minEmployees,
        maxEmployees: filters.maxEmployees,
        minFunding: filters.minFunding,
        maxFunding: filters.maxFunding,
      },
    };

    setSavedSearches([newSearch, ...savedSearches]);
    setSaveSearchName("");
    setShowSaveDialog(false);
  }, [saveSearchName, inputValue, filters, savedSearches]);

  const loadSavedSearch = useCallback((search: SavedSearch) => {
    isLoadingSavedSearchRef.current = true;

    setInputValue(search.query);
    filters.setSelectedLocations(search.filters.locations);
    filters.setSelectedIndustries(search.filters.industries);
    filters.setSelectedTargetMarkets(search.filters.targetMarkets);
    filters.setSelectedStages(search.filters.stages);
    filters.setSelectedBusinessModels(search.filters.businessModels);
    filters.setSelectedRevenueModels(search.filters.revenueModels);
    filters.setMinEmployees(search.filters.minEmployees);
    filters.setMaxEmployees(search.filters.maxEmployees);
    filters.setMinFunding(search.filters.minFunding);
    filters.setMaxFunding(search.filters.maxFunding);
    setShowSavedSearches(false);

    setTimeout(() => {
      isLoadingSavedSearchRef.current = false;
    }, 100);
  }, [filters]);

  const deleteSavedSearch = useCallback((id: string) => {
    setSavedSearches(prev => prev.filter((s) => s.id !== id));
  }, []);

  const clearEverything = useCallback(() => {
    setInputValue("");
    filters.clearAllFilters();
    setCompanies([]);
    setError(null);
    setHasPerformedSearch(false);
  }, [filters]);

  const hasSearched = hasPerformedSearch || isLoading;
  const activeFilterCount =
    filters.selectedLocations.length +
    filters.selectedIndustries.length +
    filters.selectedTargetMarkets.length +
    filters.selectedStages.length +
    filters.selectedBusinessModels.length +
    filters.selectedRevenueModels.length +
    (filters.minEmployees !== null || filters.maxEmployees !== null ? 1 : 0) +
    (filters.minFunding !== null || filters.maxFunding !== null ? 1 : 0);

  return (
    <div className="min-h-screen w-full bg-white">
      {hasSearched && (
        <div className="sticky top-0 z-10 bg-white border-b border-gray-200 shadow-md">
          <div className="w-full max-w-5xl mx-auto px-6 py-5">
            <div className="flex items-center gap-6">
              <div className={isLoading ? "animate-spin" : ""}>
                <svg className="w-9 h-9 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>

              <div className="flex-1 relative">
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={isLoading}
                  className="w-full h-12 px-5 pr-28 rounded-full border-2 border-gray-200 bg-white text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
                  placeholder={placeholder}
                />
                <button
                  onClick={handleSubmit}
                  disabled={(!inputValue.trim() && !filters.hasActiveFilters) || isLoading}
                  className="absolute right-2 top-1/2 -translate-y-1/2 px-5 py-2 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm font-semibold disabled:from-gray-300 disabled:to-gray-300 disabled:cursor-not-allowed transition-all hover:shadow-lg hover:scale-105 disabled:hover:scale-100"
                >
                  {isLoading ? "..." : "Search"}
                </button>
              </div>

              <button
                onClick={() => setShowSaveDialog(true)}
                className="px-4 py-2 rounded-full bg-green-100 text-green-700 text-sm font-medium hover:bg-green-200 transition-all hover:shadow-md flex items-center gap-1.5 border border-green-200"
                title="Save this search"
              >
                💾 Save
              </button>

              <button
                onClick={() => setShowSavedSearches(!showSavedSearches)}
                className="px-4 py-2 rounded-full bg-purple-100 text-purple-700 text-sm font-medium hover:bg-purple-200 transition-all hover:shadow-md flex items-center gap-1.5 border border-purple-200"
                title="View saved searches"
              >
                📂 Saved {savedSearches.length > 0 && `(${savedSearches.length})`}
              </button>

              {(inputValue.trim() || filters.hasActiveFilters) && (
                <button
                  onClick={clearEverything}
                  className="px-4 py-2 rounded-full bg-red-50 text-red-700 text-sm font-medium hover:bg-red-100 transition-all hover:shadow-md flex items-center gap-1.5 border border-red-200"
                  title="Clear everything"
                >
                  ✕ Clear all
                </button>
              )}
            </div>

            <div className="mt-4">
              {!filtersExpanded && (
                <div className="flex items-center gap-2 flex-wrap">
                  <button
                    onClick={() => setFiltersExpanded(true)}
                    className="px-3 py-1.5 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium transition-all flex items-center gap-1.5 border border-gray-200"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    {filters.hasActiveFilters ? `${activeFilterCount} filters` : "Add filters"}
                  </button>

                  {filters.hasActiveFilters && (
                    <FilterPills
                      {...filters}
                      onRemoveFilter={filters.removeFilterValue}
                      onClearEmployeeRange={() => {
                        filters.setMinEmployees(null);
                        filters.setMaxEmployees(null);
                      }}
                      onClearFundingRange={() => {
                        filters.setMinFunding(null);
                        filters.setMaxFunding(null);
                      }}
                    />
                  )}
                </div>
              )}

              {filtersExpanded && (
                <FilterPanel
                  filterOptions={filterOptions}
                  {...filters}
                  onRemoveFilter={filters.removeFilterValue}
                  isLoading={isLoading}
                  onClose={() => setFiltersExpanded(false)}
                />
              )}
            </div>
          </div>
        </div>
      )}

      <div className={`w-full max-w-5xl mx-auto transition-all duration-500 ${hasSearched ? "pt-8" : "min-h-screen flex flex-col justify-center"}`}>
        {!hasSearched && (
          <div className="flex flex-col items-center gap-6 px-6 mb-20">
            <div className={`mb-8 ${isLoading ? "animate-bounce" : ""}`}>
              <svg className="w-24 h-24 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>

            <div className="relative w-full max-w-3xl">
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
                disabled={(!inputValue.trim() && !filters.hasActiveFilters) || isLoading}
                className="absolute bottom-4 right-4 px-6 py-2.5 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm font-semibold disabled:from-gray-300 disabled:to-gray-300 disabled:cursor-not-allowed transition-all hover:shadow-lg hover:scale-105 disabled:hover:scale-100"
              >
                {isLoading ? "Searching..." : "Search"}
              </button>
            </div>

            <div className="w-full max-w-3xl">
              {!filtersExpanded && (
                <div className="flex items-center gap-2 flex-wrap">
                  <button
                    onClick={() => setFiltersExpanded(true)}
                    className="px-4 py-2 rounded-full bg-white border-2 border-gray-300 hover:border-blue-400 text-gray-700 text-sm font-medium transition-all hover:shadow-md flex items-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    {filters.hasActiveFilters ? `Filters (${activeFilterCount})` : "Add filters"}
                  </button>

                  {savedSearches.length > 0 && (
                    <button
                      onClick={() => setShowSavedSearches(true)}
                      className="px-4 py-2 rounded-full bg-white border-2 border-purple-300 hover:border-purple-400 text-purple-700 text-sm font-medium transition-all hover:shadow-md flex items-center gap-2"
                      title="View saved searches"
                    >
                      📂 Saved ({savedSearches.length})
                    </button>
                  )}

                  {filters.hasActiveFilters && (
                    <FilterPills
                      {...filters}
                      onRemoveFilter={filters.removeFilterValue}
                      onClearEmployeeRange={() => {
                        filters.setMinEmployees(null);
                        filters.setMaxEmployees(null);
                      }}
                      onClearFundingRange={() => {
                        filters.setMinFunding(null);
                        filters.setMaxFunding(null);
                      }}
                      showEmojis
                    />
                  )}
                </div>
              )}

              {filtersExpanded && (
                <div className="mt-4">
                  <FilterPanel
                    filterOptions={filterOptions}
                    {...filters}
                    onRemoveFilter={filters.removeFilterValue}
                    isLoading={isLoading}
                    onClose={() => setFiltersExpanded(false)}
                  />
                </div>
              )}
            </div>
          </div>
        )}

        {hasSearched && (
          <div className="w-full max-w-5xl mx-auto px-6 mt-8">
            {isLoading && (
              <>
                <div className="mb-8">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-3xl">✨</span>
                    <h2 className="text-2xl font-bold text-gray-900">Searching...</h2>
                  </div>
                  <p className="text-gray-600 ml-12">Finding the best matches for your query</p>
                </div>
                <CompanyListSkeleton count={3} />
              </>
            )}

            {error && (
              <div className="w-full p-6 rounded-3xl bg-red-50 shadow-lg border border-red-100">
                <p className="text-red-800 font-medium">{error}</p>
              </div>
            )}

            {companies.length === 0 && !isLoading && !error && (
              <EmptyState
                query={inputValue}
                hasFilters={filters.hasActiveFilters}
                onClearEverything={clearEverything}
              />
            )}

            {companies.length > 0 && !isLoading && (
              <div className="w-full">
                <div className="mb-8">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-3xl">✨</span>
                    <h2 className="text-2xl font-bold text-gray-900">
                      Found {companies.length} {companies.length === 1 ? "company" : "companies"}
                    </h2>
                  </div>
                  <p className="text-gray-600 ml-12">Here are the best matches for your search</p>
                </div>

                <div className="space-y-6">
                  {companies.map((company) => (
                    <CompanyCard key={company.id} company={company} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <SaveSearchDialog
        show={showSaveDialog}
        searchName={saveSearchName}
        onNameChange={setSaveSearchName}
        onSave={saveCurrentSearch}
        onClose={() => {
          setShowSaveDialog(false);
          setSaveSearchName("");
        }}
      />

      <SavedSearchesModal
        show={showSavedSearches}
        searches={savedSearches}
        onClose={() => setShowSavedSearches(false)}
        onLoad={loadSavedSearch}
        onDelete={deleteSavedSearch}
      />
    </div>
  );
}

export default App;

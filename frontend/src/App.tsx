import "./App.css";
import { useState, useEffect } from "react";
import axios from "axios";
import { Autocomplete, TextField, Chip } from "@mui/material";

interface Company {
  id: number;
  company_name: string;
  company_id: number | null;
  city: string | null;
  description: string | null;
  website_url: string | null;
}

interface FilterOptions {
  locations: string[];
  industries: string[];
  target_markets: string[];
  stages: string[];
}

const exampleQueries = [
  "fintech startups in New York",
  "AI B2B SaaS in San Francisco",
  "martech and adtech startups",
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
  const [selectedLocation, setSelectedLocation] = useState<string | null>(null);
  const [selectedIndustries, setSelectedIndustries] = useState<string[]>([]);
  const [selectedTargetMarkets, setSelectedTargetMarkets] = useState<string[]>([]);
  const [selectedStages, setSelectedStages] = useState<string[]>([]);
  const [minEmployees, setMinEmployees] = useState<string>("");
  const [maxEmployees, setMaxEmployees] = useState<string>("");
  const [minFunding, setMinFunding] = useState<string>("");
  const [maxFunding, setMaxFunding] = useState<string>("");

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

  const handleSubmit = async () => {
    if (!inputValue.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post("http://localhost:8000/api/submit-query", {
        query: inputValue,
        location: selectedLocation || undefined,
        industries: selectedIndustries.length > 0 ? selectedIndustries : undefined,
        target_markets: selectedTargetMarkets.length > 0 ? selectedTargetMarkets : undefined,
        stages: selectedStages.length > 0 ? selectedStages : undefined,
        min_employees: minEmployees ? parseInt(minEmployees) : undefined,
        max_employees: maxEmployees ? parseInt(maxEmployees) : undefined,
        min_funding: minFunding ? parseInt(minFunding) : undefined,
        max_funding: maxFunding ? parseInt(maxFunding) : undefined,
      });

      setCompanies(response.data.companies);
      setInputValue("");
    } catch (err) {
      setError("Failed to submit query. Please try again.");
      console.error("Error submitting query:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && inputValue.trim()) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#F5F5F0] flex items-center justify-center p-4">
      <div className="w-full max-w-2xl flex flex-col items-center gap-6">
        <h1 className="text-2xl font-medium text-gray-800 text-center">
          What are you looking for?
        </h1>

        {/* Filters */}
        <div className="w-full flex flex-col gap-3">
          <Autocomplete
            value={selectedLocation}
            onChange={(_, newValue) => setSelectedLocation(newValue)}
            options={filterOptions.locations}
            renderInput={(params) => (
              <TextField {...params} label="Location" placeholder="Select a city" size="small" />
            )}
            disabled={isLoading}
            className="bg-white rounded-lg"
          />

          <Autocomplete
            multiple
            value={selectedIndustries}
            onChange={(_, newValue) => setSelectedIndustries(newValue)}
            options={filterOptions.industries}
            renderInput={(params) => (
              <TextField {...params} label="Industries" placeholder="Select industries" size="small" />
            )}
            renderTags={(value, getTagProps) =>
              value.map((option, index) => (
                <Chip label={option} size="small" {...getTagProps({ index })} />
              ))
            }
            disabled={isLoading}
            className="bg-white rounded-lg"
          />

          <Autocomplete
            multiple
            value={selectedTargetMarkets}
            onChange={(_, newValue) => setSelectedTargetMarkets(newValue)}
            options={filterOptions.target_markets}
            renderInput={(params) => (
              <TextField {...params} label="Target Markets" placeholder="Select target markets" size="small" />
            )}
            renderTags={(value, getTagProps) =>
              value.map((option, index) => (
                <Chip label={option} size="small" {...getTagProps({ index })} />
              ))
            }
            disabled={isLoading}
            className="bg-white rounded-lg"
          />

          <Autocomplete
            multiple
            value={selectedStages}
            onChange={(_, newValue) => setSelectedStages(newValue)}
            options={filterOptions.stages}
            renderInput={(params) => (
              <TextField {...params} label="Funding Stage" placeholder="Select funding stages" size="small" />
            )}
            renderTags={(value, getTagProps) =>
              value.map((option, index) => (
                <Chip label={option} size="small" {...getTagProps({ index })} />
              ))
            }
            disabled={isLoading}
            className="bg-white rounded-lg"
          />

          <div className="flex gap-3">
            <TextField
              label="Min Employees"
              placeholder="e.g. 10"
              type="number"
              size="small"
              value={minEmployees}
              onChange={(e) => setMinEmployees(e.target.value)}
              disabled={isLoading}
              className="bg-white rounded-lg flex-1"
            />
            <TextField
              label="Max Employees"
              placeholder="e.g. 500"
              type="number"
              size="small"
              value={maxEmployees}
              onChange={(e) => setMaxEmployees(e.target.value)}
              disabled={isLoading}
              className="bg-white rounded-lg flex-1"
            />
          </div>

          <div className="flex gap-3">
            <TextField
              label="Min Funding ($)"
              placeholder="e.g. 1000000"
              type="number"
              size="small"
              value={minFunding}
              onChange={(e) => setMinFunding(e.target.value)}
              disabled={isLoading}
              className="bg-white rounded-lg flex-1"
            />
            <TextField
              label="Max Funding ($)"
              placeholder="e.g. 50000000"
              type="number"
              size="small"
              value={maxFunding}
              onChange={(e) => setMaxFunding(e.target.value)}
              disabled={isLoading}
              className="bg-white rounded-lg flex-1"
            />
          </div>
        </div>

        <div className="relative w-full">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            className="w-full h-24 px-4 py-3 pr-14 rounded-2xl border border-gray-300 bg-white text-gray-800 placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-gray-400 focus:border-transparent shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
            placeholder={placeholder}
          />
          <button
            onClick={handleSubmit}
            disabled={!inputValue.trim() || isLoading}
            className="absolute bottom-3 right-3 px-3 py-1.5 rounded-full bg-black text-white text-sm font-medium disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors hover:bg-gray-800 disabled:hover:bg-gray-300"
            aria-label="Submit"
          >
            {isLoading ? "..." : "Search"}
          </button>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="w-full p-6 rounded-2xl bg-white shadow-sm border border-gray-200">
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 border-2 border-gray-300 border-t-gray-800 rounded-full animate-spin"></div>
              <p className="text-gray-600">Searching...</p>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="w-full p-6 rounded-2xl bg-red-50 shadow-sm border border-red-200">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Results */}
        {companies.length > 0 && !isLoading && (
          <div className="w-full space-y-4">
            <h2 className="text-lg font-semibold text-gray-800">
              Found {companies.length} companies
            </h2>
            {companies.map((company) => (
              <div
                key={company.id}
                className="p-6 rounded-2xl bg-white shadow-sm border border-gray-200"
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {company.company_name}
                </h3>
                {company.city && (
                  <p className="text-sm text-gray-600 mb-2">
                    📍 {company.city}
                  </p>
                )}
                {company.description && (
                  <p className="text-gray-700 mb-3 line-clamp-3">
                    {company.description}
                  </p>
                )}
                {company.website_url && (
                  <a
                    href={company.website_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 text-sm underline"
                  >
                    Visit website
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

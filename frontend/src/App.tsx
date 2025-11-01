import "./App.css";
import { useState, useEffect } from "react";
import axios from "axios";

interface Company {
  id: number;
  company_name: string;
  company_id: number | null;
  city: string | null;
  description: string | null;
  website_url: string | null;
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

  useEffect(() => {
    // Randomly select a placeholder on component mount
    const randomQuery = exampleQueries[Math.floor(Math.random() * exampleQueries.length)];
    setPlaceholder(`e.g. ${randomQuery}`);
  }, []);

  const handleSubmit = async () => {
    if (!inputValue.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post("http://localhost:8000/api/submit-query", {
        query: inputValue,
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

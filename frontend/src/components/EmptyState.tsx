interface EmptyStateProps {
  query: string;
  hasFilters: boolean;
  onClearEverything: () => void;
}

export const EmptyState = ({ query, hasFilters }: EmptyStateProps) => {
  return (
    <div className="w-full max-w-2xl mx-auto text-center py-16">
      <div className="mb-6">
        <svg
          className="w-32 h-32 mx-auto text-gray-300"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </div>

      <h2 className="text-3xl font-bold text-gray-900 mb-3">No companies found</h2>

      {query && (
        <p className="text-lg text-gray-600 mb-2">
          We couldn't find any companies matching <span className="font-semibold text-gray-900">"{query}"</span>
        </p>
      )}

      <div className="mt-8 space-y-4">
        <p className="text-gray-600 font-medium">Try these suggestions:</p>
        <ul className="space-y-2 text-left max-w-md mx-auto">
          <li className="flex items-start gap-3 text-gray-700">
            <span className="text-blue-500 mt-1">•</span>
            <span>Use broader search terms (e.g., "fintech" instead of "cryptocurrency payment processor")</span>
          </li>
          <li className="flex items-start gap-3 text-gray-700">
            <span className="text-blue-500 mt-1">•</span>
            <span>Check your spelling and try different keywords</span>
          </li>
          {hasFilters && (
            <li className="flex items-start gap-3 text-gray-700">
              <span className="text-blue-500 mt-1">•</span>
              <span>Remove some filters to expand your results</span>
            </li>
          )}
          <li className="flex items-start gap-3 text-gray-700">
            <span className="text-blue-500 mt-1">•</span>
            <span>Try searching for industries or business models instead of specific features</span>
          </li>
        </ul>
      </div>
    </div>
  );
};

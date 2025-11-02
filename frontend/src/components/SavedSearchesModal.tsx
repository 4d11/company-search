import { SavedSearch } from "../types";

interface SavedSearchesModalProps {
  show: boolean;
  searches: SavedSearch[];
  onClose: () => void;
  onLoad: (search: SavedSearch) => void;
  onDelete: (id: string) => void;
}

export const SavedSearchesModal = ({ show, searches, onClose, onLoad, onDelete }: SavedSearchesModalProps) => {
  if (!show) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-3xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-2xl font-bold text-gray-900">📂 Saved Searches</h3>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 text-2xl transition-colors flex items-center justify-center"
            >
              ×
            </button>
          </div>
          <p className="text-gray-600 mt-1">Click to load a search, or delete ones you no longer need.</p>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {searches.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-400 text-lg">No saved searches yet</p>
              <p className="text-gray-500 text-sm mt-2">Save your first search to get started!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {searches.map((search) => (
                <div key={search.id} className="p-5 rounded-2xl bg-white border-2 border-gray-200 hover:border-blue-300 hover:shadow-lg transition-all group">
                  <div className="flex items-start justify-between gap-4">
                    <button onClick={() => onLoad(search)} className="flex-1 text-left">
                      <h4 className="font-bold text-gray-900 text-lg mb-2 group-hover:text-blue-600 transition-colors">
                        {search.name}
                      </h4>
                      {search.query && (
                        <p className="text-gray-600 text-sm mb-3 line-clamp-1">
                          "{search.query}"
                        </p>
                      )}
                      <div className="flex items-center gap-2 flex-wrap">
                        {search.filters.locations.length > 0 && (
                          <span className="text-xs px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                            📍 {search.filters.locations.length} location{search.filters.locations.length > 1 ? 's' : ''}
                          </span>
                        )}
                        {search.filters.industries.length > 0 && (
                          <span className="text-xs px-2.5 py-1 rounded-full bg-purple-50 text-purple-700 border border-purple-200">
                            🏢 {search.filters.industries.length} industr{search.filters.industries.length > 1 ? 'ies' : 'y'}
                          </span>
                        )}
                        {search.filters.stages.length > 0 && (
                          <span className="text-xs px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                            🚀 {search.filters.stages.length} stage{search.filters.stages.length > 1 ? 's' : ''}
                          </span>
                        )}
                        <span className="text-xs text-gray-500">
                          {new Date(search.timestamp).toLocaleDateString()}
                        </span>
                      </div>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(search.id);
                      }}
                      className="flex-shrink-0 w-8 h-8 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 text-lg transition-colors flex items-center justify-center"
                      title="Delete search"
                    >
                      ×
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

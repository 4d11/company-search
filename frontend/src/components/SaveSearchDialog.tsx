interface SaveSearchDialogProps {
  show: boolean;
  searchName: string;
  onNameChange: (name: string) => void;
  onSave: () => void;
  onClose: () => void;
}

export const SaveSearchDialog = ({ show, searchName, onNameChange, onSave, onClose }: SaveSearchDialogProps) => {
  if (!show) return null;

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') onSave();
    if (e.key === 'Escape') onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full p-6">
        <h3 className="text-2xl font-bold text-gray-900 mb-4">💾 Save Search</h3>
        <p className="text-gray-600 mb-4">Give this search a name so you can quickly access it later.</p>
        <input
          type="text"
          value={searchName}
          onChange={(e) => onNameChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="e.g., Early-stage AI startups"
          className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-400 mb-4"
          autoFocus
        />
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 rounded-xl bg-gray-100 text-gray-700 font-medium hover:bg-gray-200 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onSave}
            disabled={!searchName.trim()}
            className="flex-1 px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold hover:shadow-lg disabled:from-gray-300 disabled:to-gray-300 disabled:cursor-not-allowed transition-all"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

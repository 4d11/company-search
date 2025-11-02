import { Typography } from "@mui/material";

interface ThesisContext {
  thesis_type?: string;
  investment_thesis?: string;
  strategic_focus?: string;
  key_criteria?: string[];
  market_insights?: string;
  reasoning?: string;
}

interface ThesisContextCardProps {
  thesisContext: ThesisContext;
}

export const ThesisContextCard = ({ thesisContext }: ThesisContextCardProps) => {
  return (
    <div className="p-8 rounded-3xl bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50 border-2 border-purple-200 shadow-lg mb-6">
      <div className="flex items-start gap-3 mb-4">
        <span className="text-3xl">🎯</span>
        <div className="flex-1">
          <Typography variant="h5" className="font-bold text-purple-900 mb-1">
            Investment Thesis Context
          </Typography>
          {thesisContext.thesis_type && (
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-100 border border-purple-300">
              <span className="text-xs font-semibold text-purple-800 uppercase tracking-wide">
                {thesisContext.thesis_type}
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="space-y-4">
        {thesisContext.investment_thesis && (
          <div className="bg-white rounded-xl p-4 border border-purple-100">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">💡</span>
              <Typography variant="subtitle1" className="font-semibold text-gray-900">
                Investment Thesis
              </Typography>
            </div>
            <Typography variant="body2" className="text-gray-700 leading-relaxed">
              {thesisContext.investment_thesis}
            </Typography>
          </div>
        )}

        {thesisContext.strategic_focus && (
          <div className="bg-white rounded-xl p-4 border border-blue-100">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">🎯</span>
              <Typography variant="subtitle1" className="font-semibold text-gray-900">
                Strategic Focus
              </Typography>
            </div>
            <Typography variant="body2" className="text-gray-700 leading-relaxed">
              {thesisContext.strategic_focus}
            </Typography>
          </div>
        )}

        {thesisContext.key_criteria && thesisContext.key_criteria.length > 0 && (
          <div className="bg-white rounded-xl p-4 border border-indigo-100">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">✅</span>
              <Typography variant="subtitle1" className="font-semibold text-gray-900">
                Key Selection Criteria
              </Typography>
            </div>
            <ul className="space-y-2">
              {thesisContext.key_criteria.map((criterion, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-indigo-600 mt-0.5">•</span>
                  <Typography variant="body2" className="text-gray-700 flex-1">
                    {criterion}
                  </Typography>
                </li>
              ))}
            </ul>
          </div>
        )}

        {thesisContext.market_insights && (
          <div className="bg-white rounded-xl p-4 border border-teal-100">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">📊</span>
              <Typography variant="subtitle1" className="font-semibold text-gray-900">
                Market Insights
              </Typography>
            </div>
            <Typography variant="body2" className="text-gray-700 leading-relaxed">
              {thesisContext.market_insights}
            </Typography>
          </div>
        )}

        {thesisContext.reasoning && (
          <div className="bg-white rounded-xl p-4 border border-amber-100">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">🧠</span>
              <Typography variant="subtitle1" className="font-semibold text-gray-900">
                Strategic Reasoning
              </Typography>
            </div>
            <Typography variant="body2" className="text-gray-700 leading-relaxed">
              {thesisContext.reasoning}
            </Typography>
          </div>
        )}
      </div>

      <div className="mt-4 pt-4 border-t border-purple-200">
        <Typography variant="caption" className="text-purple-700 italic">
          💡 This analysis helps you understand the strategic rationale behind these company recommendations
        </Typography>
      </div>
    </div>
  );
};

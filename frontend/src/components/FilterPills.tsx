import { FILTER_CONFIG, NUMERIC_FILTER_CONFIG } from "../constants/filters";

interface FilterPillsProps {
  selectedLocations: string[];
  selectedIndustries: string[];
  selectedTargetMarkets: string[];
  selectedStages: string[];
  selectedBusinessModels: string[];
  selectedRevenueModels: string[];
  minEmployees: number | null;
  maxEmployees: number | null;
  minFunding: number | null;
  maxFunding: number | null;
  onRemoveFilter: (segment: string, op: string, value: string | number) => void;
  onClearEmployeeRange: () => void;
  onClearFundingRange: () => void;
  showEmojis?: boolean;
}

export const FilterPills = ({
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
  onRemoveFilter,
  onClearEmployeeRange,
  onClearFundingRange,
  showEmojis = false,
}: FilterPillsProps) => {
  const pillClass = "px-3 py-1.5 rounded-full text-sm font-medium flex items-center gap-1.5";
  const buttonClass = "ml-1 hover:bg-opacity-20 rounded-full w-4 h-4 flex items-center justify-center text-sm font-bold transition-colors";

  return (
    <>
      {selectedLocations.map((loc) => (
        <div key={loc} className={`${pillClass} bg-blue-50 text-blue-700 border border-blue-200`}>
          {showEmojis && `${FILTER_CONFIG.location.emoji} `}{loc}
          <button onClick={() => onRemoveFilter("location", "EQ", loc)} className={`${buttonClass} text-blue-600 hover:text-blue-900 hover:bg-blue-100`}>×</button>
        </div>
      ))}
      {selectedIndustries.map((ind) => (
        <div key={ind} className={`${pillClass} bg-purple-50 text-purple-700 border border-purple-200`}>
          {showEmojis && `${FILTER_CONFIG.industries.emoji} `}{ind}
          <button onClick={() => onRemoveFilter("industries", "EQ", ind)} className={`${buttonClass} text-purple-600 hover:text-purple-900 hover:bg-purple-100`}>×</button>
        </div>
      ))}
      {selectedTargetMarkets.map((tm) => (
        <div key={tm} className={`${pillClass} bg-teal-50 text-teal-700 border border-teal-200`}>
          {showEmojis && `${FILTER_CONFIG.targetMarkets.emoji} `}{tm}
          <button onClick={() => onRemoveFilter("target_markets", "EQ", tm)} className={`${buttonClass} text-teal-600 hover:text-teal-900 hover:bg-teal-100`}>×</button>
        </div>
      ))}
      {selectedStages.map((stage) => (
        <div key={stage} className={`${pillClass} bg-amber-50 text-amber-700 border border-amber-200`}>
          {showEmojis && `${FILTER_CONFIG.stages.emoji} `}{stage}
          <button onClick={() => onRemoveFilter("funding_stage", "EQ", stage)} className={`${buttonClass} text-amber-600 hover:text-amber-900 hover:bg-amber-100`}>×</button>
        </div>
      ))}
      {selectedBusinessModels.map((bm) => (
        <div key={bm} className={`${pillClass} bg-cyan-50 text-cyan-700 border border-cyan-200`}>
          {showEmojis && `${FILTER_CONFIG.businessModels.emoji} `}{bm}
          <button onClick={() => onRemoveFilter("business_models", "EQ", bm)} className={`${buttonClass} text-cyan-600 hover:text-cyan-900 hover:bg-cyan-100`}>×</button>
        </div>
      ))}
      {selectedRevenueModels.map((rm) => (
        <div key={rm} className={`${pillClass} bg-pink-50 text-pink-700 border border-pink-200`}>
          {showEmojis && `${FILTER_CONFIG.revenueModels.emoji} `}{rm}
          <button onClick={() => onRemoveFilter("revenue_models", "EQ", rm)} className={`${buttonClass} text-pink-600 hover:text-pink-900 hover:bg-pink-100`}>×</button>
        </div>
      ))}
      {(minEmployees !== null || maxEmployees !== null) && (
        <div className={`${pillClass} bg-indigo-50 text-indigo-700 border border-indigo-200`}>
          {showEmojis && `${NUMERIC_FILTER_CONFIG.employee.emoji} `}{minEmployees || 0}–{maxEmployees || '∞'} employees
          <button onClick={onClearEmployeeRange} className={`${buttonClass} text-indigo-600 hover:text-indigo-900 hover:bg-indigo-100`}>×</button>
        </div>
      )}
      {(minFunding !== null || maxFunding !== null) && (
        <div className={`${pillClass} bg-emerald-50 text-emerald-700 border border-emerald-200`}>
          {showEmojis && `${NUMERIC_FILTER_CONFIG.funding.emoji} `}${minFunding || 0}–${maxFunding || '∞'}
          <button onClick={onClearFundingRange} className={`${buttonClass} text-emerald-600 hover:text-emerald-900 hover:bg-emerald-100`}>×</button>
        </div>
      )}
    </>
  );
};

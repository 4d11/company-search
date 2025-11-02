import { FilterAutocomplete } from "./FilterAutocomplete";
import { NumericRangeFilter } from "./NumericRangeFilter";
import { FILTER_CONFIG, NUMERIC_FILTER_CONFIG } from "../constants/filters";
import { FilterOptions } from "../types";

interface FilterPanelProps {
  filterOptions: FilterOptions;
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
  setSelectedLocations: (val: string[]) => void;
  setSelectedIndustries: (val: string[]) => void;
  setSelectedTargetMarkets: (val: string[]) => void;
  setSelectedStages: (val: string[]) => void;
  setSelectedBusinessModels: (val: string[]) => void;
  setSelectedRevenueModels: (val: string[]) => void;
  setMinEmployees: (val: number | null) => void;
  setMaxEmployees: (val: number | null) => void;
  setMinFunding: (val: number | null) => void;
  setMaxFunding: (val: number | null) => void;
  onRemoveFilter: (segment: string, op: string, value: string | number) => void;
  isLoading: boolean;
  onClose: () => void;
}

export const FilterPanel = ({
  filterOptions,
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
  setSelectedLocations,
  setSelectedIndustries,
  setSelectedTargetMarkets,
  setSelectedStages,
  setSelectedBusinessModels,
  setSelectedRevenueModels,
  setMinEmployees,
  setMaxEmployees,
  setMinFunding,
  setMaxFunding,
  onRemoveFilter,
  isLoading,
  onClose,
}: FilterPanelProps) => {
  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Filters</h3>
        <button onClick={onClose} className="text-xs text-gray-600 hover:text-gray-800 font-medium transition-colors">
          Done
        </button>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4">
        <FilterAutocomplete
          value={selectedLocations}
          onChange={setSelectedLocations}
          onDeleteChip={(val) => onRemoveFilter("location", "EQ", val)}
          options={filterOptions.locations}
          label={FILTER_CONFIG.location.label}
          emoji={FILTER_CONFIG.location.emoji}
          chipColor={FILTER_CONFIG.location.colors}
          disabled={isLoading}
        />
        <FilterAutocomplete
          value={selectedIndustries}
          onChange={setSelectedIndustries}
          onDeleteChip={(val) => onRemoveFilter("industries", "EQ", val)}
          options={filterOptions.industries}
          label={FILTER_CONFIG.industries.label}
          emoji={FILTER_CONFIG.industries.emoji}
          chipColor={FILTER_CONFIG.industries.colors}
          disabled={isLoading}
        />
        <FilterAutocomplete
          value={selectedTargetMarkets}
          onChange={setSelectedTargetMarkets}
          onDeleteChip={(val) => onRemoveFilter("target_markets", "EQ", val)}
          options={filterOptions.target_markets}
          label={FILTER_CONFIG.targetMarkets.label}
          emoji={FILTER_CONFIG.targetMarkets.emoji}
          chipColor={FILTER_CONFIG.targetMarkets.colors}
          disabled={isLoading}
        />
        <FilterAutocomplete
          value={selectedStages}
          onChange={setSelectedStages}
          onDeleteChip={(val) => onRemoveFilter("funding_stage", "EQ", val)}
          options={filterOptions.stages}
          label={FILTER_CONFIG.stages.label}
          emoji={FILTER_CONFIG.stages.emoji}
          chipColor={FILTER_CONFIG.stages.colors}
          disabled={isLoading}
        />
        <FilterAutocomplete
          value={selectedBusinessModels}
          onChange={setSelectedBusinessModels}
          onDeleteChip={(val) => onRemoveFilter("business_models", "EQ", val)}
          options={filterOptions.business_models}
          label={FILTER_CONFIG.businessModels.label}
          emoji={FILTER_CONFIG.businessModels.emoji}
          chipColor={FILTER_CONFIG.businessModels.colors}
          disabled={isLoading}
        />
        <FilterAutocomplete
          value={selectedRevenueModels}
          onChange={setSelectedRevenueModels}
          onDeleteChip={(val) => onRemoveFilter("revenue_models", "EQ", val)}
          options={filterOptions.revenue_models}
          label={FILTER_CONFIG.revenueModels.label}
          emoji={FILTER_CONFIG.revenueModels.emoji}
          chipColor={FILTER_CONFIG.revenueModels.colors}
          disabled={isLoading}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <NumericRangeFilter
          minValue={minEmployees}
          maxValue={maxEmployees}
          onMinChange={setMinEmployees}
          onMaxChange={setMaxEmployees}
          label={NUMERIC_FILTER_CONFIG.employee.label}
          emoji={NUMERIC_FILTER_CONFIG.employee.emoji}
          chipColor={NUMERIC_FILTER_CONFIG.employee.colors}
          disabled={isLoading}
        />
        <NumericRangeFilter
          minValue={minFunding}
          maxValue={maxFunding}
          onMinChange={setMinFunding}
          onMaxChange={setMaxFunding}
          label={NUMERIC_FILTER_CONFIG.funding.label}
          emoji={NUMERIC_FILTER_CONFIG.funding.emoji}
          chipColor={NUMERIC_FILTER_CONFIG.funding.colors}
          disabled={isLoading}
        />
      </div>
    </div>
  );
};

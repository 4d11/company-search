export const API_BASE_URL = 'http://localhost:8000';

export const API_ENDPOINTS = {
  FILTER_OPTIONS: `${API_BASE_URL}/api/filter-options`,
  SUBMIT_QUERY: `${API_BASE_URL}/api/submit-query`,
} as const;

export const FILTER_COLORS = {
  location: { bg: '#DBEAFE', text: '#1E40AF' },
  industries: { bg: '#E8EAFF', text: '#4F46E5' },
  targetMarkets: { bg: '#DCFCE7', text: '#15803D' },
  stages: { bg: '#FEF3C7', text: '#92400E' },
} as const;

export const FILTER_CONFIG = {
  location: {
    label: 'Locations',
    emoji: '📍',
    colors: FILTER_COLORS.location,
  },
  industries: {
    label: 'Industries',
    emoji: '🏢',
    colors: FILTER_COLORS.industries,
  },
  targetMarkets: {
    label: 'Target Markets',
    emoji: '🎯',
    colors: FILTER_COLORS.targetMarkets,
  },
  stages: {
    label: 'Funding Stage',
    emoji: '🚀',
    colors: FILTER_COLORS.stages,
  },
  businessModels: {
    label: 'Business Models',
    emoji: '💼',
    colors: { bg: '#F3E8FF', text: '#6B21A8' }, // Purple tint
  },
  revenueModels: {
    label: 'Revenue Models',
    emoji: '💵',
    colors: { bg: '#FEF9C3', text: '#854D0E' }, // Amber tint
  },
} as const;

export const NUMERIC_FILTER_CONFIG = {
  employee: {
    label: 'Employee Count',
    emoji: '👥',
    colors: { bg: 'bg-indigo-50', text: 'text-indigo-800', border: 'border-indigo-200' },
  },
  funding: {
    label: 'Funding Amount (USD)',
    emoji: '💰',
    colors: { bg: 'bg-emerald-50', text: 'text-emerald-800', border: 'border-emerald-200' },
  },
} as const;

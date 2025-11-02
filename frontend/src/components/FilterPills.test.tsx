import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FilterPills } from './FilterPills';

describe('FilterPills', () => {
  const defaultProps = {
    selectedLocations: [],
    selectedIndustries: [],
    selectedTargetMarkets: [],
    selectedStages: [],
    selectedBusinessModels: [],
    selectedRevenueModels: [],
    minEmployees: null,
    maxEmployees: null,
    minFunding: null,
    maxFunding: null,
    onRemoveFilter: vi.fn(),
    onClearEmployeeRange: vi.fn(),
    onClearFundingRange: vi.fn(),
    showEmojis: false,
  };

  it('should render location pills', () => {
    render(<FilterPills {...defaultProps} selectedLocations={['New York', 'San Francisco']} />);

    expect(screen.getByText('New York')).toBeInTheDocument();
    expect(screen.getByText('San Francisco')).toBeInTheDocument();
  });

  it('should render industry pills', () => {
    render(<FilterPills {...defaultProps} selectedIndustries={['Fintech', 'AI']} />);

    expect(screen.getByText('Fintech')).toBeInTheDocument();
    expect(screen.getByText('AI')).toBeInTheDocument();
  });

  it('should show emojis when showEmojis is true', () => {
    render(
      <FilterPills
        {...defaultProps}
        selectedLocations={['NYC']}
        showEmojis={true}
      />
    );

    const pill = screen.getByText(/NYC/);
    expect(pill.textContent).toContain('📍');
  });

  it('should not show emojis when showEmojis is false', () => {
    render(
      <FilterPills
        {...defaultProps}
        selectedLocations={['NYC']}
        showEmojis={false}
      />
    );

    const pill = screen.getByText('NYC');
    expect(pill.textContent).not.toContain('📍');
  });

  it('should render employee count range pill', () => {
    render(<FilterPills {...defaultProps} minEmployees={10} maxEmployees={100} />);

    expect(screen.getByText(/10–100 employees/)).toBeInTheDocument();
  });

  it('should render funding range pill with infinity symbol', () => {
    const { container } = render(<FilterPills {...defaultProps} minFunding={100000} maxFunding={null} />);

    expect(container.textContent).toContain('100000');
    expect(container.textContent).toContain('∞');
  });

  it('should call onRemoveFilter when close button is clicked', async () => {
    const user = userEvent.setup();
    const onRemoveFilter = vi.fn();

    render(
      <FilterPills
        {...defaultProps}
        selectedLocations={['NYC']}
        onRemoveFilter={onRemoveFilter}
      />
    );

    const closeButton = screen.getByRole('button');
    await user.click(closeButton);

    expect(onRemoveFilter).toHaveBeenCalledWith('location', 'EQ', 'NYC');
  });

  it('should call onClearEmployeeRange when employee range close is clicked', async () => {
    const user = userEvent.setup();
    const onClearEmployeeRange = vi.fn();

    render(
      <FilterPills
        {...defaultProps}
        minEmployees={10}
        maxEmployees={100}
        onClearEmployeeRange={onClearEmployeeRange}
      />
    );

    const closeButton = screen.getByRole('button');
    await user.click(closeButton);

    expect(onClearEmployeeRange).toHaveBeenCalled();
  });

  it('should render multiple filter types together', () => {
    render(
      <FilterPills
        {...defaultProps}
        selectedLocations={['NYC']}
        selectedIndustries={['Tech']}
        selectedStages={['Series A']}
        minEmployees={50}
      />
    );

    expect(screen.getByText('NYC')).toBeInTheDocument();
    expect(screen.getByText('Tech')).toBeInTheDocument();
    expect(screen.getByText('Series A')).toBeInTheDocument();
    expect(screen.getByText(/50–∞ employees/)).toBeInTheDocument();
  });

  it('should not render anything when no filters are active', () => {
    const { container } = render(<FilterPills {...defaultProps} />);
    expect(container.firstChild).toBeNull();
  });

  it('should apply correct color classes for different filter types', () => {
    render(
      <FilterPills
        {...defaultProps}
        selectedLocations={['NYC']}
        selectedIndustries={['Tech']}
      />
    );

    const locationPill = screen.getByText('NYC').closest('div');
    expect(locationPill).toHaveClass('bg-blue-50');
    expect(locationPill).toHaveClass('text-blue-700');

    const industryPill = screen.getByText('Tech').closest('div');
    expect(industryPill).toHaveClass('bg-purple-50');
    expect(industryPill).toHaveClass('text-purple-700');
  });
});

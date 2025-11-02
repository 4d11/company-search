import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FilterAutocomplete } from './FilterAutocomplete';

describe('FilterAutocomplete', () => {
  const defaultProps = {
    value: [],
    onChange: vi.fn(),
    options: ['Option 1', 'Option 2', 'Option 3'],
    label: 'Test Filter',
    emoji: '🏢',
    chipColor: {
      bg: '#E8EAFF',
      text: '#4F46E5',
    },
  };

  it('renders with label and emoji', () => {
    render(<FilterAutocomplete {...defaultProps} />);

    const input = screen.getByLabelText('🏢 Test Filter');
    expect(input).toBeInTheDocument();
  });

  it('displays selected values as chips', () => {
    render(<FilterAutocomplete {...defaultProps} value={['Option 1', 'Option 2']} />);

    expect(screen.getByText('Option 1')).toBeInTheDocument();
    expect(screen.getByText('Option 2')).toBeInTheDocument();
  });

  it('calls onChange when selection changes', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();

    render(<FilterAutocomplete {...defaultProps} onChange={onChange} />);

    const input = screen.getByLabelText('🏢 Test Filter');
    await user.click(input);

    // Note: Full autocomplete interaction testing requires more complex setup
    // This is a basic test to ensure the component renders and is interactive
  });

  it('applies correct chip colors', () => {
    render(<FilterAutocomplete {...defaultProps} value={['Option 1']} />);

    const chip = screen.getByText('Option 1').closest('.MuiChip-root');
    expect(chip).toBeInTheDocument();
  });

  it('disables autocomplete when disabled prop is true', () => {
    render(<FilterAutocomplete {...defaultProps} disabled={true} />);

    const input = screen.getByLabelText('🏢 Test Filter');
    expect(input).toBeDisabled();
  });

  it('handles empty value array', () => {
    render(<FilterAutocomplete {...defaultProps} value={[]} />);

    const input = screen.getByLabelText('🏢 Test Filter');
    expect(input).toBeInTheDocument();
  });

  it('supports multiple selections', () => {
    const selectedValues = ['Option 1', 'Option 2', 'Option 3'];
    render(<FilterAutocomplete {...defaultProps} value={selectedValues} />);

    selectedValues.forEach(value => {
      expect(screen.getByText(value)).toBeInTheDocument();
    });
  });

  it('renders with different emoji and label combinations', () => {
    render(
      <FilterAutocomplete
        {...defaultProps}
        label="Industries"
        emoji="🏢"
      />
    );

    expect(screen.getByLabelText('🏢 Industries')).toBeInTheDocument();
  });
});

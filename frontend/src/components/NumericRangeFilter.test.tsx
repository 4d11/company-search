import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NumericRangeFilter } from './NumericRangeFilter';

describe('NumericRangeFilter', () => {
  const defaultProps = {
    minValue: null,
    maxValue: null,
    onMinChange: vi.fn(),
    onMaxChange: vi.fn(),
    label: 'Employee Count',
    emoji: '👥',
    chipColor: { bg: 'bg-indigo-50', text: 'text-indigo-800', border: 'border-indigo-200' },
  };

  it('renders with label and emoji', () => {
    render(<NumericRangeFilter {...defaultProps} />);

    expect(screen.getByText('👥')).toBeInTheDocument();
    expect(screen.getByText('Employee Count')).toBeInTheDocument();
  });

  it('renders min and max input fields', () => {
    render(<NumericRangeFilter {...defaultProps} />);

    const minInput = screen.getByLabelText('Min');
    const maxInput = screen.getByLabelText('Max');

    expect(minInput).toBeInTheDocument();
    expect(maxInput).toBeInTheDocument();
  });

  it('displays placeholder text', () => {
    render(<NumericRangeFilter {...defaultProps} />);

    const minInput = screen.getByPlaceholderText('0');
    const maxInput = screen.getByPlaceholderText('∞');

    expect(minInput).toBeInTheDocument();
    expect(maxInput).toBeInTheDocument();
  });

  it('displays current min and max values', () => {
    render(<NumericRangeFilter {...defaultProps} minValue={100} maxValue={500} />);

    const minInput = screen.getByLabelText('Min') as HTMLInputElement;
    const maxInput = screen.getByLabelText('Max') as HTMLInputElement;

    expect(minInput.value).toBe('100');
    expect(maxInput.value).toBe('500');
  });

  it('calls onMinChange when min input changes', async () => {
    const user = userEvent.setup();
    const onMinChange = vi.fn();

    render(<NumericRangeFilter {...defaultProps} onMinChange={onMinChange} />);

    const minInput = screen.getByLabelText('Min');
    await user.type(minInput, '50');

    expect(onMinChange).toHaveBeenCalled();
  });

  it('calls onMaxChange when max input changes', async () => {
    const user = userEvent.setup();
    const onMaxChange = vi.fn();

    render(<NumericRangeFilter {...defaultProps} onMaxChange={onMaxChange} />);

    const maxInput = screen.getByLabelText('Max');
    await user.type(maxInput, '500');

    expect(onMaxChange).toHaveBeenCalled();
  });

  it('calls onMinChange with null when input is cleared', async () => {
    const user = userEvent.setup();
    const onMinChange = vi.fn();

    render(<NumericRangeFilter {...defaultProps} minValue={100} onMinChange={onMinChange} />);

    const minInput = screen.getByLabelText('Min');
    await user.clear(minInput);

    expect(onMinChange).toHaveBeenCalledWith(null);
  });

  it('disables inputs when disabled prop is true', () => {
    render(<NumericRangeFilter {...defaultProps} disabled={true} />);

    const minInput = screen.getByLabelText('Min');
    const maxInput = screen.getByLabelText('Max');

    expect(minInput).toBeDisabled();
    expect(maxInput).toBeDisabled();
  });

  it('handles empty values correctly', () => {
    render(<NumericRangeFilter {...defaultProps} minValue={null} maxValue={null} />);

    const minInput = screen.getByLabelText('Min') as HTMLInputElement;
    const maxInput = screen.getByLabelText('Max') as HTMLInputElement;

    expect(minInput.value).toBe('');
    expect(maxInput.value).toBe('');
  });

  it('accepts text input for formatted numbers', () => {
    render(<NumericRangeFilter {...defaultProps} />);

    const minInput = screen.getByLabelText('Min') as HTMLInputElement;

    expect(minInput.type).toBe('text');
  });
});

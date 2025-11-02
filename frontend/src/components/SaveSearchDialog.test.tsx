import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SaveSearchDialog } from './SaveSearchDialog';

describe('SaveSearchDialog', () => {
  const defaultProps = {
    show: true,
    searchName: '',
    onNameChange: vi.fn(),
    onSave: vi.fn(),
    onClose: vi.fn(),
  };

  it('should not render when show is false', () => {
    const { container } = render(<SaveSearchDialog {...defaultProps} show={false} />);
    expect(container.firstChild).toBeNull();
  });

  it('should render when show is true', () => {
    render(<SaveSearchDialog {...defaultProps} />);
    expect(screen.getByText('💾 Save Search')).toBeInTheDocument();
  });

  it('should display the input field', () => {
    render(<SaveSearchDialog {...defaultProps} />);
    const input = screen.getByPlaceholderText(/Early-stage AI startups/i);
    expect(input).toBeInTheDocument();
  });

  it('should call onNameChange when typing in input', async () => {
    const user = userEvent.setup();
    const onNameChange = vi.fn();

    render(<SaveSearchDialog {...defaultProps} onNameChange={onNameChange} />);

    const input = screen.getByPlaceholderText(/Early-stage AI startups/i);
    await user.type(input, 'My Search');

    expect(onNameChange).toHaveBeenCalled();
  });

  it('should display the current search name in input', () => {
    render(<SaveSearchDialog {...defaultProps} searchName="Fintech Companies" />);
    const input = screen.getByDisplayValue('Fintech Companies');
    expect(input).toBeInTheDocument();
  });

  it('should have Save and Cancel buttons', () => {
    render(<SaveSearchDialog {...defaultProps} />);

    expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
  });

  it('should call onSave when Save button is clicked', async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();

    render(<SaveSearchDialog {...defaultProps} searchName="Test" onSave={onSave} />);

    const saveButton = screen.getByRole('button', { name: /save/i });
    await user.click(saveButton);

    expect(onSave).toHaveBeenCalled();
  });

  it('should call onClose when Cancel button is clicked', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(<SaveSearchDialog {...defaultProps} onClose={onClose} />);

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await user.click(cancelButton);

    expect(onClose).toHaveBeenCalled();
  });

  it('should disable Save button when search name is empty', () => {
    render(<SaveSearchDialog {...defaultProps} searchName="" />);
    const saveButton = screen.getByRole('button', { name: /save/i });
    expect(saveButton).toBeDisabled();
  });

  it('should enable Save button when search name has content', () => {
    render(<SaveSearchDialog {...defaultProps} searchName="My Search" />);
    const saveButton = screen.getByRole('button', { name: /save/i });
    expect(saveButton).not.toBeDisabled();
  });

  it('should call onSave when Enter key is pressed', async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();

    render(<SaveSearchDialog {...defaultProps} searchName="Test" onSave={onSave} />);

    const input = screen.getByPlaceholderText(/Early-stage AI startups/i);
    await user.click(input);
    await user.keyboard('{Enter}');

    expect(onSave).toHaveBeenCalled();
  });

  it('should call onClose when Escape key is pressed', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(<SaveSearchDialog {...defaultProps} onClose={onClose} />);

    const input = screen.getByPlaceholderText(/Early-stage AI startups/i);
    await user.click(input);
    await user.keyboard('{Escape}');

    expect(onClose).toHaveBeenCalled();
  });

  it('should render an input field with proper attributes', () => {
    render(<SaveSearchDialog {...defaultProps} />);
    const input = screen.getByPlaceholderText(/Early-stage AI startups/i) as HTMLInputElement;
    expect(input).toBeInTheDocument();
    expect(input.type).toBe('text');
  });
});

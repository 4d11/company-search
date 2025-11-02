import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EmptyState } from './EmptyState';

describe('EmptyState', () => {
  const defaultProps = {
    query: '',
    hasFilters: false,
    onClearEverything: () => {},
  };

  it('should render the no results message', () => {
    render(<EmptyState {...defaultProps} />);
    expect(screen.getByText('No companies found')).toBeInTheDocument();
  });

  it('should display the search query when provided', () => {
    render(<EmptyState {...defaultProps} query="fintech startups" />);
    expect(screen.getByText(/fintech startups/i)).toBeInTheDocument();
  });

  it('should not display query message when query is empty', () => {
    render(<EmptyState {...defaultProps} query="" />);
    expect(screen.queryByText(/We couldn't find any companies matching/i)).not.toBeInTheDocument();
  });

  it('should show suggestion to remove filters when hasFilters is true', () => {
    render(<EmptyState {...defaultProps} hasFilters={true} />);
    expect(screen.getByText(/Remove some filters to expand your results/i)).toBeInTheDocument();
  });

  it('should not show filter suggestion when hasFilters is false', () => {
    render(<EmptyState {...defaultProps} hasFilters={false} />);
    expect(screen.queryByText(/Remove some filters to expand your results/i)).not.toBeInTheDocument();
  });

  it('should show all general suggestions', () => {
    render(<EmptyState {...defaultProps} />);

    expect(screen.getByText(/Use broader search terms/i)).toBeInTheDocument();
    expect(screen.getByText(/Check your spelling/i)).toBeInTheDocument();
    expect(screen.getByText(/Try searching for industries or business models/i)).toBeInTheDocument();
  });

  it('should render the icon', () => {
    const { container } = render(<EmptyState {...defaultProps} />);
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('should have accessible structure', () => {
    render(<EmptyState {...defaultProps} query="AI companies" />);

    const heading = screen.getByText('No companies found');
    expect(heading.tagName).toBe('H2');
  });
});

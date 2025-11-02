import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CompanyCard } from './CompanyCard';

describe('CompanyCard', () => {
  const mockCompany = {
    id: 1,
    company_name: 'Test Company',
    company_id: 123,
    city: 'San Francisco',
    description: 'A test company description',
    website_url: 'https://example.com',
    employee_count: 100,
    stage: 'Series A',
    funding_amount: 5000000,
    location: 'San Francisco',
    industries: ['FinTech', 'AI/ML'],
    target_markets: ['Enterprise', 'SMB'],
    explanation: 'This company matches your search criteria',
  };

  it('renders company name', () => {
    render(<CompanyCard company={mockCompany} />);
    expect(screen.getByText('Test Company')).toBeInTheDocument();
  });

  it('displays company initial in avatar', () => {
    render(<CompanyCard company={mockCompany} />);
    expect(screen.getByText('T')).toBeInTheDocument();
  });

  it('shows explanation when provided', () => {
    render(<CompanyCard company={mockCompany} />);
    expect(screen.getByText(/Why this company\?/)).toBeInTheDocument();
    expect(screen.getByText('This company matches your search criteria')).toBeInTheDocument();
  });

  it('hides explanation when not provided', () => {
    const companyWithoutExplanation = { ...mockCompany, explanation: null };
    render(<CompanyCard company={companyWithoutExplanation} />);
    expect(screen.queryByText('✨ Why this company?')).not.toBeInTheDocument();
  });

  it('displays company description', () => {
    render(<CompanyCard company={mockCompany} />);
    expect(screen.getByText('A test company description')).toBeInTheDocument();
  });

  it('renders industries with emoji', () => {
    render(<CompanyCard company={mockCompany} />);
    expect(screen.getByText(/🏢 FinTech/)).toBeInTheDocument();
    expect(screen.getByText(/🏢 AI\/ML/)).toBeInTheDocument();
  });

  it('renders target markets with emoji', () => {
    render(<CompanyCard company={mockCompany} />);
    expect(screen.getByText(/🎯 Enterprise/)).toBeInTheDocument();
    expect(screen.getByText(/🎯 SMB/)).toBeInTheDocument();
  });

  it('displays funding stage', () => {
    render(<CompanyCard company={mockCompany} />);
    expect(screen.getByText(/🚀 Series A/)).toBeInTheDocument();
  });

  it('formats funding amount in millions', () => {
    render(<CompanyCard company={mockCompany} />);
    expect(screen.getByText(/💰 \$5.0M/)).toBeInTheDocument();
  });

  it('displays employee count', () => {
    render(<CompanyCard company={mockCompany} />);
    expect(screen.getByText(/👥 100 employees/)).toBeInTheDocument();
  });

  it('shows location', () => {
    render(<CompanyCard company={mockCompany} />);
    expect(screen.getByText(/📍 San Francisco/)).toBeInTheDocument();
  });

  it('renders website link with correct attributes', () => {
    render(<CompanyCard company={mockCompany} />);
    const link = screen.getByText('🔗 Website').closest('a');
    expect(link).toHaveAttribute('href', 'https://example.com');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('handles missing optional fields gracefully', () => {
    const minimalCompany = {
      id: 1,
      company_name: 'Minimal Company',
      company_id: null,
      city: null,
      description: null,
      website_url: null,
      employee_count: null,
      stage: null,
      funding_amount: null,
      location: null,
      industries: [],
      target_markets: [],
      explanation: null,
    };

    render(<CompanyCard company={minimalCompany} />);
    expect(screen.getByText('Minimal Company')).toBeInTheDocument();
    expect(screen.queryByText(/💰/)).not.toBeInTheDocument();
    expect(screen.queryByText(/👥/)).not.toBeInTheDocument();
  });

  it('falls back to city when location is not provided', () => {
    const companyWithCity = { ...mockCompany, location: null, city: 'New York' };
    render(<CompanyCard company={companyWithCity} />);
    expect(screen.getByText(/📍 New York/)).toBeInTheDocument();
  });

  it('handles empty industries array', () => {
    const companyNoIndustries = { ...mockCompany, industries: [] };
    render(<CompanyCard company={companyNoIndustries} />);
    expect(screen.queryByText(/🏢/)).not.toBeInTheDocument();
  });

  it('handles empty target markets array', () => {
    const companyNoMarkets = { ...mockCompany, target_markets: [] };
    render(<CompanyCard company={companyNoMarkets} />);
    expect(screen.queryByText(/🎯/)).not.toBeInTheDocument();
  });

  it('formats large funding amounts correctly', () => {
    const companyWithLargeFunding = { ...mockCompany, funding_amount: 50000000 };
    render(<CompanyCard company={companyWithLargeFunding} />);
    expect(screen.getByText(/💰 \$50.0M/)).toBeInTheDocument();
  });
});

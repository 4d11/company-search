import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ThesisContextCard } from './ThesisContextCard';

describe('ThesisContextCard', () => {
  const fullThesisContext = {
    thesis_type: 'Portfolio Fit',
    investment_thesis: 'Focusing on early-stage AI companies with strong technical teams',
    strategic_focus: 'B2B SaaS platforms leveraging machine learning for enterprise automation',
    key_criteria: [
      'Series A or earlier funding stage',
      'AI/ML core technology',
      'Enterprise customer focus',
      'Experienced technical founders'
    ],
    market_insights: 'The enterprise AI market is experiencing rapid growth with increasing demand for automation solutions',
    reasoning: 'These companies align with our thesis of backing technically strong teams building transformative AI products'
  };

  it('renders thesis context header', () => {
    render(<ThesisContextCard thesisContext={fullThesisContext} />);
    expect(screen.getByText('Investment Thesis Context')).toBeInTheDocument();
  });

  it('displays thesis type badge', () => {
    render(<ThesisContextCard thesisContext={fullThesisContext} />);
    expect(screen.getByText(/Portfolio Fit/i)).toBeInTheDocument();
  });

  it('shows investment thesis section', () => {
    render(<ThesisContextCard thesisContext={fullThesisContext} />);
    expect(screen.getByText('Investment Thesis')).toBeInTheDocument();
    expect(screen.getByText('Focusing on early-stage AI companies with strong technical teams')).toBeInTheDocument();
  });

  it('displays strategic focus section', () => {
    render(<ThesisContextCard thesisContext={fullThesisContext} />);
    expect(screen.getByText('Strategic Focus')).toBeInTheDocument();
    expect(screen.getByText(/B2B SaaS platforms leveraging machine learning/)).toBeInTheDocument();
  });

  it('renders all key criteria as list items', () => {
    render(<ThesisContextCard thesisContext={fullThesisContext} />);
    expect(screen.getByText('Key Selection Criteria')).toBeInTheDocument();
    expect(screen.getByText('Series A or earlier funding stage')).toBeInTheDocument();
    expect(screen.getByText('AI/ML core technology')).toBeInTheDocument();
    expect(screen.getByText('Enterprise customer focus')).toBeInTheDocument();
    expect(screen.getByText('Experienced technical founders')).toBeInTheDocument();
  });

  it('shows market insights section', () => {
    render(<ThesisContextCard thesisContext={fullThesisContext} />);
    expect(screen.getByText('Market Insights')).toBeInTheDocument();
    expect(screen.getByText(/enterprise AI market is experiencing rapid growth/)).toBeInTheDocument();
  });

  it('displays strategic reasoning section', () => {
    render(<ThesisContextCard thesisContext={fullThesisContext} />);
    expect(screen.getByText('Strategic Reasoning')).toBeInTheDocument();
    expect(screen.getByText(/align with our thesis of backing technically strong teams/)).toBeInTheDocument();
  });

  it('shows footer message', () => {
    render(<ThesisContextCard thesisContext={fullThesisContext} />);
    expect(screen.getByText(/This analysis helps you understand the strategic rationale/)).toBeInTheDocument();
  });

  it('handles missing thesis_type gracefully', () => {
    const contextWithoutType = { ...fullThesisContext, thesis_type: undefined };
    render(<ThesisContextCard thesisContext={contextWithoutType} />);
    expect(screen.getByText('Investment Thesis Context')).toBeInTheDocument();
    expect(screen.queryByText('PORTFOLIO FIT')).not.toBeInTheDocument();
  });

  it('handles missing investment_thesis section', () => {
    const contextWithoutInvestmentThesis = { ...fullThesisContext, investment_thesis: undefined };
    render(<ThesisContextCard thesisContext={contextWithoutInvestmentThesis} />);
    expect(screen.queryByText('Investment Thesis')).not.toBeInTheDocument();
  });

  it('handles missing strategic_focus section', () => {
    const contextWithoutFocus = { ...fullThesisContext, strategic_focus: undefined };
    render(<ThesisContextCard thesisContext={contextWithoutFocus} />);
    expect(screen.queryByText('Strategic Focus')).not.toBeInTheDocument();
  });

  it('hides key criteria section when empty', () => {
    const contextWithoutCriteria = { ...fullThesisContext, key_criteria: [] };
    render(<ThesisContextCard thesisContext={contextWithoutCriteria} />);
    expect(screen.queryByText('Key Selection Criteria')).not.toBeInTheDocument();
  });

  it('hides key criteria section when undefined', () => {
    const contextWithoutCriteria = { ...fullThesisContext, key_criteria: undefined };
    render(<ThesisContextCard thesisContext={contextWithoutCriteria} />);
    expect(screen.queryByText('Key Selection Criteria')).not.toBeInTheDocument();
  });

  it('handles missing market_insights section', () => {
    const contextWithoutInsights = { ...fullThesisContext, market_insights: undefined };
    render(<ThesisContextCard thesisContext={contextWithoutInsights} />);
    expect(screen.queryByText('Market Insights')).not.toBeInTheDocument();
  });

  it('handles missing reasoning section', () => {
    const contextWithoutReasoning = { ...fullThesisContext, reasoning: undefined };
    render(<ThesisContextCard thesisContext={contextWithoutReasoning} />);
    expect(screen.queryByText('Strategic Reasoning')).not.toBeInTheDocument();
  });

  it('renders minimal context with only thesis_type', () => {
    const minimalContext = { thesis_type: 'Conceptual Query' };
    render(<ThesisContextCard thesisContext={minimalContext} />);
    expect(screen.getByText('Investment Thesis Context')).toBeInTheDocument();
    expect(screen.getByText(/Conceptual Query/i)).toBeInTheDocument();
  });

  it('renders empty context object', () => {
    render(<ThesisContextCard thesisContext={{}} />);
    expect(screen.getByText('Investment Thesis Context')).toBeInTheDocument();
    expect(screen.getByText(/This analysis helps you understand/)).toBeInTheDocument();
  });

  it('renders with partial data', () => {
    const partialContext = {
      thesis_type: 'Market Analysis',
      investment_thesis: 'Focus on sustainable tech',
      key_criteria: ['Climate tech', 'B2B model']
    };
    render(<ThesisContextCard thesisContext={partialContext} />);
    expect(screen.getByText(/Market Analysis/i)).toBeInTheDocument();
    expect(screen.getByText('Focus on sustainable tech')).toBeInTheDocument();
    expect(screen.getByText('Climate tech')).toBeInTheDocument();
    expect(screen.getByText('B2B model')).toBeInTheDocument();
  });
});

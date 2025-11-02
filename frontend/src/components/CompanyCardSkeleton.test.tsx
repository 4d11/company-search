import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { CompanyCardSkeleton, CompanyListSkeleton } from './CompanyCardSkeleton';

describe('CompanyCardSkeleton', () => {
  it('should render without crashing', () => {
    const { container } = render(<CompanyCardSkeleton />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it('should have pulse animation class', () => {
    const { container } = render(<CompanyCardSkeleton />);
    const skeleton = container.querySelector('.animate-pulse');
    expect(skeleton).toBeInTheDocument();
  });

  it('should match the structure of a CompanyCard', () => {
    const { container } = render(<CompanyCardSkeleton />);

    const avatar = container.querySelector('.w-16.h-16');
    expect(avatar).toBeInTheDocument();

    const skeletonElements = container.querySelectorAll('.bg-gray-200');
    expect(skeletonElements.length).toBeGreaterThan(0);
  });
});

describe('CompanyListSkeleton', () => {
  it('should render default 3 skeleton cards', () => {
    const { container } = render(<CompanyListSkeleton />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons).toHaveLength(3);
  });

  it('should render custom number of skeleton cards', () => {
    const { container } = render(<CompanyListSkeleton count={5} />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons).toHaveLength(5);
  });

  it('should render 1 skeleton when count is 1', () => {
    const { container } = render(<CompanyListSkeleton count={1} />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons).toHaveLength(1);
  });

  it('should have proper spacing between skeletons', () => {
    const { container } = render(<CompanyListSkeleton />);
    const wrapper = container.querySelector('.space-y-6');
    expect(wrapper).toBeInTheDocument();
  });
});

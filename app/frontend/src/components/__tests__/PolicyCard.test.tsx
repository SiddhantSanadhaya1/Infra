/**
 * Unit tests for PolicyCard component
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import PolicyCard from '../PolicyCard';
import { Policy } from '@/services/api';


describe('PolicyCard Component', () => {
  const mockPolicy: Policy = {
    id: 'policy-123',
    policyholder_id: 'holder-456',
    policy_type: 'AUTO',
    policy_number: 'POL-AUTO-20260330-1234',
    premium_amount: 1200,
    coverage_amount: 100000,
    start_date: '2026-01-01',
    end_date: '2026-12-31',
    status: 'ACTIVE',
  };

  describe('Basic Rendering', () => {
    it('renders policy type label', () => {
      render(<PolicyCard policy={mockPolicy} />);

      expect(screen.getByText('Auto Insurance')).toBeInTheDocument();
    });

    it('renders policy number', () => {
      render(<PolicyCard policy={mockPolicy} />);

      expect(screen.getByText('POL-AUTO-20260330-1234')).toBeInTheDocument();
    });

    it('renders policy status', () => {
      render(<PolicyCard policy={mockPolicy} />);

      expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    });

    it('renders coverage amount', () => {
      render(<PolicyCard policy={mockPolicy} />);

      expect(screen.getByText('$100,000')).toBeInTheDocument();
    });

    it('renders monthly premium', () => {
      render(<PolicyCard policy={mockPolicy} />);

      // Monthly premium = 1200 / 12 = 100
      expect(screen.getByText('$100')).toBeInTheDocument();
    });
  });

  describe('Policy Types', () => {
    it('renders AUTO policy with car icon', () => {
      render(<PolicyCard policy={mockPolicy} />);

      expect(screen.getByText('🚗')).toBeInTheDocument();
      expect(screen.getByText('Auto Insurance')).toBeInTheDocument();
    });

    it('renders HOME policy with house icon', () => {
      const homePolicy = { ...mockPolicy, policy_type: 'HOME' as const };
      render(<PolicyCard policy={homePolicy} />);

      expect(screen.getByText('🏠')).toBeInTheDocument();
      expect(screen.getByText('Home Insurance')).toBeInTheDocument();
    });

    it('renders LIFE policy with heart icon', () => {
      const lifePolicy = { ...mockPolicy, policy_type: 'LIFE' as const };
      render(<PolicyCard policy={lifePolicy} />);

      expect(screen.getByText('❤️')).toBeInTheDocument();
      expect(screen.getByText('Life Insurance')).toBeInTheDocument();
    });

    it('renders COMMERCIAL policy with building icon', () => {
      const commercialPolicy = { ...mockPolicy, policy_type: 'COMMERCIAL' as const };
      render(<PolicyCard policy={commercialPolicy} />);

      expect(screen.getByText('🏢')).toBeInTheDocument();
      expect(screen.getByText('Commercial Insurance')).toBeInTheDocument();
    });
  });

  describe('Policy Status', () => {
    it('renders ACTIVE status with green styling', () => {
      const { container } = render(<PolicyCard policy={mockPolicy} />);

      const statusBadge = container.querySelector('.bg-green-100');
      expect(statusBadge).toBeInTheDocument();
      expect(statusBadge).toHaveTextContent('ACTIVE');
    });

    it('renders EXPIRED status with gray styling', () => {
      const expiredPolicy = { ...mockPolicy, status: 'EXPIRED' as const };
      const { container } = render(<PolicyCard policy={expiredPolicy} />);

      const statusBadge = container.querySelector('.bg-gray-100');
      expect(statusBadge).toBeInTheDocument();
      expect(statusBadge).toHaveTextContent('EXPIRED');
    });

    it('renders CANCELLED status with red styling', () => {
      const cancelledPolicy = { ...mockPolicy, status: 'CANCELLED' as const };
      const { container } = render(<PolicyCard policy={cancelledPolicy} />);

      const statusBadge = container.querySelector('.bg-red-100');
      expect(statusBadge).toBeInTheDocument();
      expect(statusBadge).toHaveTextContent('CANCELLED');
    });

    it('renders PENDING status with yellow styling', () => {
      const pendingPolicy = { ...mockPolicy, status: 'PENDING' as const };
      const { container } = render(<PolicyCard policy={pendingPolicy} />);

      const statusBadge = container.querySelector('.bg-yellow-100');
      expect(statusBadge).toBeInTheDocument();
      expect(statusBadge).toHaveTextContent('PENDING');
    });
  });

  describe('Date Formatting', () => {
    it('formats start date correctly', () => {
      render(<PolicyCard policy={mockPolicy} />);

      expect(screen.getByText(/Effective: Jan 1, 2026/)).toBeInTheDocument();
    });

    it('formats end date correctly', () => {
      render(<PolicyCard policy={mockPolicy} />);

      expect(screen.getByText(/Expires: Dec 31, 2026/)).toBeInTheDocument();
    });
  });

  describe('Expiring Soon Warning', () => {
    it('shows warning for policy expiring in 15 days', () => {
      const today = new Date();
      const expiringDate = new Date(today);
      expiringDate.setDate(today.getDate() + 15);

      const expiringPolicy = {
        ...mockPolicy,
        end_date: expiringDate.toISOString().split('T')[0],
      };

      render(<PolicyCard policy={expiringPolicy} />);

      expect(screen.getByText(/expires within 30 days/i)).toBeInTheDocument();
      expect(screen.getByText(/(soon)/)).toBeInTheDocument();
    });

    it('shows warning for policy expiring in 1 day', () => {
      const today = new Date();
      const expiringDate = new Date(today);
      expiringDate.setDate(today.getDate() + 1);

      const expiringPolicy = {
        ...mockPolicy,
        end_date: expiringDate.toISOString().split('T')[0],
      };

      render(<PolicyCard policy={expiringPolicy} />);

      expect(screen.getByText(/Contact InsureCo to renew/i)).toBeInTheDocument();
    });

    it('does not show warning for policy expiring in 31 days', () => {
      const today = new Date();
      const expiringDate = new Date(today);
      expiringDate.setDate(today.getDate() + 31);

      const expiringPolicy = {
        ...mockPolicy,
        end_date: expiringDate.toISOString().split('T')[0],
      };

      render(<PolicyCard policy={expiringPolicy} />);

      expect(screen.queryByText(/expires within 30 days/i)).not.toBeInTheDocument();
    });

    it('does not show warning for policy expiring in 60 days', () => {
      const today = new Date();
      const expiringDate = new Date(today);
      expiringDate.setDate(today.getDate() + 60);

      const expiringPolicy = {
        ...mockPolicy,
        end_date: expiringDate.toISOString().split('T')[0],
      };

      render(<PolicyCard policy={expiringPolicy} />);

      expect(screen.queryByText(/(soon)/)).not.toBeInTheDocument();
    });

    it('does not show warning for already expired policy', () => {
      const today = new Date();
      const expiredDate = new Date(today);
      expiredDate.setDate(today.getDate() - 1);

      const expiredPolicy = {
        ...mockPolicy,
        end_date: expiredDate.toISOString().split('T')[0],
      };

      render(<PolicyCard policy={expiredPolicy} />);

      expect(screen.queryByText(/expires within 30 days/i)).not.toBeInTheDocument();
    });
  });

  describe('Premium Calculations', () => {
    it('calculates monthly premium correctly from annual', () => {
      const policy = { ...mockPolicy, premium_amount: 2400 };
      render(<PolicyCard policy={policy} />);

      // 2400 / 12 = 200
      expect(screen.getByText('$200')).toBeInTheDocument();
    });

    it('handles string premium amount', () => {
      const policy = { ...mockPolicy, premium_amount: '3600' };
      render(<PolicyCard policy={policy} />);

      // 3600 / 12 = 300
      expect(screen.getByText('$300')).toBeInTheDocument();
    });

    it('handles decimal premium amount', () => {
      const policy = { ...mockPolicy, premium_amount: 1234.56 };
      render(<PolicyCard policy={policy} />);

      // 1234.56 / 12 ≈ 102.88
      const monthlyText = screen.getByText(/\$10[0-9]/);
      expect(monthlyText).toBeInTheDocument();
    });

    it('formats coverage amount with no decimals', () => {
      const policy = { ...mockPolicy, coverage_amount: 250000 };
      render(<PolicyCard policy={policy} />);

      expect(screen.getByText('$250,000')).toBeInTheDocument();
    });

    it('handles string coverage amount', () => {
      const policy = { ...mockPolicy, coverage_amount: '500000' };
      render(<PolicyCard policy={policy} />);

      expect(screen.getByText('$500,000')).toBeInTheDocument();
    });
  });

  describe('Card Styling', () => {
    it('has card class', () => {
      const { container } = render(<PolicyCard policy={mockPolicy} />);

      const card = container.querySelector('.card');
      expect(card).toBeInTheDocument();
    });

    it('has hover effect class', () => {
      const { container } = render(<PolicyCard policy={mockPolicy} />);

      const card = container.querySelector('.hover\\:shadow-md');
      expect(card).toBeInTheDocument();
    });

    it('has transition class', () => {
      const { container } = render(<PolicyCard policy={mockPolicy} />);

      const card = container.querySelector('.transition-shadow');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles zero premium amount', () => {
      const policy = { ...mockPolicy, premium_amount: 0 };
      render(<PolicyCard policy={policy} />);

      expect(screen.getByText('$0')).toBeInTheDocument();
    });

    it('handles zero coverage amount', () => {
      const policy = { ...mockPolicy, coverage_amount: 0 };
      render(<PolicyCard policy={policy} />);

      expect(screen.getByText('$0')).toBeInTheDocument();
    });

    it('handles very large coverage amount', () => {
      const policy = { ...mockPolicy, coverage_amount: 10000000 };
      render(<PolicyCard policy={policy} />);

      expect(screen.getByText('$10,000,000')).toBeInTheDocument();
    });

    it('handles very small premium amount', () => {
      const policy = { ...mockPolicy, premium_amount: 12 };
      render(<PolicyCard policy={policy} />);

      // 12 / 12 = 1
      expect(screen.getByText('$1')).toBeInTheDocument();
    });
  });

  describe('Layout and Structure', () => {
    it('displays all key information', () => {
      render(<PolicyCard policy={mockPolicy} />);

      // Check all major sections are present
      expect(screen.getByText('Auto Insurance')).toBeInTheDocument();
      expect(screen.getByText('POL-AUTO-20260330-1234')).toBeInTheDocument();
      expect(screen.getByText('ACTIVE')).toBeInTheDocument();
      expect(screen.getByText('Coverage Amount')).toBeInTheDocument();
      expect(screen.getByText('Monthly Premium')).toBeInTheDocument();
    });

    it('has flex layout', () => {
      const { container } = render(<PolicyCard policy={mockPolicy} />);

      const flexElements = container.querySelectorAll('.flex');
      expect(flexElements.length).toBeGreaterThan(0);
    });

    it('has grid layout for amounts', () => {
      const { container } = render(<PolicyCard policy={mockPolicy} />);

      const grid = container.querySelector('.grid');
      expect(grid).toBeInTheDocument();
    });
  });
});

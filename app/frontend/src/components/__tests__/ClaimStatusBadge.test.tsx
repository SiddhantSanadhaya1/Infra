/**
 * Unit tests for ClaimStatusBadge component
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ClaimStatusBadge from '../ClaimStatusBadge';


describe('ClaimStatusBadge Component', () => {
  describe('Status Rendering', () => {
    it('renders SUBMITTED status', () => {
      render(<ClaimStatusBadge status="SUBMITTED" />);

      expect(screen.getByText('Submitted')).toBeInTheDocument();
    });

    it('renders UNDER_REVIEW status', () => {
      render(<ClaimStatusBadge status="UNDER_REVIEW" />);

      expect(screen.getByText('Under Review')).toBeInTheDocument();
    });

    it('renders APPROVED status', () => {
      render(<ClaimStatusBadge status="APPROVED" />);

      expect(screen.getByText('Approved')).toBeInTheDocument();
    });

    it('renders REJECTED status', () => {
      render(<ClaimStatusBadge status="REJECTED" />);

      expect(screen.getByText('Rejected')).toBeInTheDocument();
    });

    it('renders PAID status', () => {
      render(<ClaimStatusBadge status="PAID" />);

      expect(screen.getByText('Paid')).toBeInTheDocument();
    });

    it('renders unknown status with default styling', () => {
      render(<ClaimStatusBadge status="UNKNOWN_STATUS" />);

      expect(screen.getByText('UNKNOWN_STATUS')).toBeInTheDocument();
    });

    it('renders empty string status', () => {
      render(<ClaimStatusBadge status="" />);

      const badge = screen.getByText('');
      expect(badge).toBeInTheDocument();
    });
  });

  describe('Color Classes', () => {
    it('applies blue classes for SUBMITTED status', () => {
      const { container } = render(<ClaimStatusBadge status="SUBMITTED" />);

      const badge = container.querySelector('.bg-blue-100');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('text-blue-700', 'border-blue-200');
    });

    it('applies purple classes for UNDER_REVIEW status', () => {
      const { container } = render(<ClaimStatusBadge status="UNDER_REVIEW" />);

      const badge = container.querySelector('.bg-purple-100');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('text-purple-700', 'border-purple-200');
    });

    it('applies green classes for APPROVED status', () => {
      const { container } = render(<ClaimStatusBadge status="APPROVED" />);

      const badge = container.querySelector('.bg-green-100');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('text-green-700', 'border-green-200');
    });

    it('applies red classes for REJECTED status', () => {
      const { container } = render(<ClaimStatusBadge status="REJECTED" />);

      const badge = container.querySelector('.bg-red-100');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('text-red-700', 'border-red-200');
    });

    it('applies emerald classes for PAID status', () => {
      const { container } = render(<ClaimStatusBadge status="PAID" />);

      const badge = container.querySelector('.bg-emerald-100');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('text-emerald-700', 'border-emerald-200');
    });

    it('applies default gray classes for unknown status', () => {
      const { container } = render(<ClaimStatusBadge status="CUSTOM_STATUS" />);

      const badge = container.querySelector('.bg-gray-100');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('text-gray-600', 'border-gray-200');
    });
  });

  describe('Badge Styling', () => {
    it('has inline-flex class', () => {
      const { container } = render(<ClaimStatusBadge status="SUBMITTED" />);

      const badge = container.querySelector('.inline-flex');
      expect(badge).toBeInTheDocument();
    });

    it('has items-center class', () => {
      const { container } = render(<ClaimStatusBadge status="APPROVED" />);

      const badge = container.querySelector('.items-center');
      expect(badge).toBeInTheDocument();
    });

    it('has padding classes', () => {
      const { container } = render(<ClaimStatusBadge status="PAID" />);

      const badge = container.querySelector('.px-2');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('py-0.5');
    });

    it('has rounded class', () => {
      const { container } = render(<ClaimStatusBadge status="SUBMITTED" />);

      const badge = container.querySelector('.rounded');
      expect(badge).toBeInTheDocument();
    });

    it('has border class', () => {
      const { container } = render(<ClaimStatusBadge status="APPROVED" />);

      const badge = container.querySelector('.border');
      expect(badge).toBeInTheDocument();
    });

    it('has text size and font classes', () => {
      const { container } = render(<ClaimStatusBadge status="REJECTED" />);

      const badge = container.querySelector('.text-xs');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('font-medium');
    });
  });

  describe('Label Formatting', () => {
    it('formats SUBMITTED correctly', () => {
      render(<ClaimStatusBadge status="SUBMITTED" />);

      expect(screen.getByText('Submitted')).toBeInTheDocument();
      expect(screen.queryByText('SUBMITTED')).not.toBeInTheDocument();
    });

    it('formats UNDER_REVIEW with spaces', () => {
      render(<ClaimStatusBadge status="UNDER_REVIEW" />);

      expect(screen.getByText('Under Review')).toBeInTheDocument();
      expect(screen.queryByText('UNDER_REVIEW')).not.toBeInTheDocument();
    });

    it('preserves unknown status text as-is', () => {
      render(<ClaimStatusBadge status="MY_CUSTOM_STATUS" />);

      expect(screen.getByText('MY_CUSTOM_STATUS')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles lowercase status', () => {
      render(<ClaimStatusBadge status="submitted" />);

      expect(screen.getByText('submitted')).toBeInTheDocument();
    });

    it('handles mixed case status', () => {
      render(<ClaimStatusBadge status="Under_Review" />);

      expect(screen.getByText('Under_Review')).toBeInTheDocument();
    });

    it('handles status with special characters', () => {
      render(<ClaimStatusBadge status="STATUS-123" />);

      expect(screen.getByText('STATUS-123')).toBeInTheDocument();
    });

    it('handles very long status text', () => {
      const longStatus = 'VERY_LONG_STATUS_NAME_THAT_MIGHT_OVERFLOW';
      render(<ClaimStatusBadge status={longStatus} />);

      expect(screen.getByText(longStatus)).toBeInTheDocument();
    });

    it('handles status with numbers', () => {
      render(<ClaimStatusBadge status="STATUS_123" />);

      expect(screen.getByText('STATUS_123')).toBeInTheDocument();
    });
  });

  describe('Multiple Instances', () => {
    it('renders multiple badges with different statuses', () => {
      const { container } = render(
        <>
          <ClaimStatusBadge status="SUBMITTED" />
          <ClaimStatusBadge status="APPROVED" />
          <ClaimStatusBadge status="PAID" />
        </>
      );

      expect(screen.getByText('Submitted')).toBeInTheDocument();
      expect(screen.getByText('Approved')).toBeInTheDocument();
      expect(screen.getByText('Paid')).toBeInTheDocument();

      // Check that all badges are rendered
      const badges = container.querySelectorAll('span');
      expect(badges.length).toBe(3);
    });

    it('renders same status multiple times', () => {
      const { container } = render(
        <>
          <ClaimStatusBadge status="APPROVED" />
          <ClaimStatusBadge status="APPROVED" />
        </>
      );

      const approvedBadges = screen.getAllByText('Approved');
      expect(approvedBadges).toHaveLength(2);
    });
  });

  describe('Component Structure', () => {
    it('renders as a span element', () => {
      const { container } = render(<ClaimStatusBadge status="SUBMITTED" />);

      const span = container.querySelector('span');
      expect(span).toBeInTheDocument();
    });

    it('contains only text content', () => {
      const { container } = render(<ClaimStatusBadge status="APPROVED" />);

      const badge = container.querySelector('span');
      expect(badge).toBeInTheDocument();
      expect(badge?.textContent).toBe('Approved');
    });
  });
});

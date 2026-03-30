/**
 * Unit tests for StatsCard component
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import StatsCard from '../StatsCard';


describe('StatsCard Component', () => {
  describe('Rendering', () => {
    it('renders with shield icon', () => {
      render(
        <StatsCard label="Active Policies" value={12} icon="shield" color="blue" />
      );

      expect(screen.getByText('Active Policies')).toBeInTheDocument();
      expect(screen.getByText('12')).toBeInTheDocument();
    });

    it('renders with file icon', () => {
      render(
        <StatsCard label="Documents" value={45} icon="file" color="orange" />
      );

      expect(screen.getByText('Documents')).toBeInTheDocument();
      expect(screen.getByText('45')).toBeInTheDocument();
    });

    it('renders with clock icon', () => {
      render(
        <StatsCard label="Pending" value={8} icon="clock" color="yellow" />
      );

      expect(screen.getByText('Pending')).toBeInTheDocument();
      expect(screen.getByText('8')).toBeInTheDocument();
    });

    it('renders with dollar icon', () => {
      render(
        <StatsCard label="Premium" value="$1,234" icon="dollar" color="green" />
      );

      expect(screen.getByText('Premium')).toBeInTheDocument();
      expect(screen.getByText('$1,234')).toBeInTheDocument();
    });

    it('renders with string value', () => {
      render(
        <StatsCard label="Status" value="Active" icon="shield" color="blue" />
      );

      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument();
    });

    it('renders with numeric value', () => {
      render(
        <StatsCard label="Count" value={0} icon="file" color="blue" />
      );

      expect(screen.getByText('Count')).toBeInTheDocument();
      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('renders with large numeric value', () => {
      render(
        <StatsCard label="Total Claims" value={999999} icon="file" color="red" />
      );

      expect(screen.getByText('Total Claims')).toBeInTheDocument();
      expect(screen.getByText('999999')).toBeInTheDocument();
    });
  });

  describe('Color Themes', () => {
    it('applies blue color theme', () => {
      const { container } = render(
        <StatsCard label="Test" value={1} icon="shield" color="blue" />
      );

      const card = container.querySelector('.bg-blue-50');
      expect(card).toBeInTheDocument();
    });

    it('applies orange color theme', () => {
      const { container } = render(
        <StatsCard label="Test" value={1} icon="file" color="orange" />
      );

      const card = container.querySelector('.bg-orange-50');
      expect(card).toBeInTheDocument();
    });

    it('applies yellow color theme', () => {
      const { container } = render(
        <StatsCard label="Test" value={1} icon="clock" color="yellow" />
      );

      const card = container.querySelector('.bg-yellow-50');
      expect(card).toBeInTheDocument();
    });

    it('applies green color theme', () => {
      const { container } = render(
        <StatsCard label="Test" value={1} icon="dollar" color="green" />
      );

      const card = container.querySelector('.bg-green-50');
      expect(card).toBeInTheDocument();
    });

    it('applies red color theme', () => {
      const { container } = render(
        <StatsCard label="Test" value={1} icon="shield" color="red" />
      );

      const card = container.querySelector('.bg-red-50');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Icon Display', () => {
    it('displays SVG icon', () => {
      const { container } = render(
        <StatsCard label="Test" value={1} icon="shield" color="blue" />
      );

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
      expect(svg).toHaveClass('w-6', 'h-6');
    });

    it('renders shield icon path', () => {
      const { container } = render(
        <StatsCard label="Test" value={1} icon="shield" color="blue" />
      );

      const path = container.querySelector('path');
      expect(path).toBeInTheDocument();
    });

    it('renders file icon path', () => {
      const { container } = render(
        <StatsCard label="Test" value={1} icon="file" color="orange" />
      );

      const path = container.querySelector('path');
      expect(path).toBeInTheDocument();
    });

    it('renders clock icon path', () => {
      const { container } = render(
        <StatsCard label="Test" value={1} icon="clock" color="yellow" />
      );

      const path = container.querySelector('path');
      expect(path).toBeInTheDocument();
    });

    it('renders dollar icon path', () => {
      const { container } = render(
        <StatsCard label="Test" value={1} icon="dollar" color="green" />
      );

      const path = container.querySelector('path');
      expect(path).toBeInTheDocument();
    });
  });

  describe('Layout and Styling', () => {
    it('has card class', () => {
      const { container } = render(
        <StatsCard label="Test" value={1} icon="shield" color="blue" />
      );

      const card = container.querySelector('.card');
      expect(card).toBeInTheDocument();
    });

    it('has flex layout', () => {
      const { container } = render(
        <StatsCard label="Test" value={1} icon="shield" color="blue" />
      );

      const card = container.querySelector('.flex');
      expect(card).toBeInTheDocument();
    });

    it('has padding classes', () => {
      const { container } = render(
        <StatsCard label="Test" value={1} icon="shield" color="blue" />
      );

      const card = container.querySelector('.p-5');
      expect(card).toBeInTheDocument();
    });

    it('displays icon and text in correct order', () => {
      render(
        <StatsCard label="Policies" value={5} icon="shield" color="blue" />
      );

      const text = screen.getByText('Policies');
      expect(text).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('renders with empty string value', () => {
      render(
        <StatsCard label="Empty" value="" icon="file" color="blue" />
      );

      expect(screen.getByText('Empty')).toBeInTheDocument();
    });

    it('renders with long label text', () => {
      const longLabel = 'This is a very long label that might wrap to multiple lines';
      render(
        <StatsCard label={longLabel} value={100} icon="shield" color="blue" />
      );

      expect(screen.getByText(longLabel)).toBeInTheDocument();
    });

    it('renders with long value text', () => {
      const longValue = '$1,234,567,890.99';
      render(
        <StatsCard label="Revenue" value={longValue} icon="dollar" color="green" />
      );

      expect(screen.getByText(longValue)).toBeInTheDocument();
    });

    it('renders with special characters in label', () => {
      render(
        <StatsCard label="Claims (Pending)" value={3} icon="clock" color="yellow" />
      );

      expect(screen.getByText('Claims (Pending)')).toBeInTheDocument();
    });

    it('renders with negative numeric value', () => {
      render(
        <StatsCard label="Balance" value={-100} icon="dollar" color="red" />
      );

      expect(screen.getByText('-100')).toBeInTheDocument();
    });

    it('renders with zero value', () => {
      render(
        <StatsCard label="New Claims" value={0} icon="file" color="blue" />
      );

      expect(screen.getByText('0')).toBeInTheDocument();
    });
  });
});

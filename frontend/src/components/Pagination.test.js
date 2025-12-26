import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Pagination from './Pagination';

describe('Pagination Component', () => {
  const mockOnPageChange = jest.fn();

  beforeEach(() => {
    mockOnPageChange.mockClear();
  });

  test('renders pagination with correct page numbers', () => {
    render(
      <Pagination
        currentPage={1}
        totalPages={5}
        onPageChange={mockOnPageChange}
        itemsPerPage={20}
        totalItems={100}
      />
    );

    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  test('shows correct items info', () => {
    render(
      <Pagination
        currentPage={2}
        totalPages={5}
        onPageChange={mockOnPageChange}
        itemsPerPage={20}
        totalItems={100}
      />
    );

    expect(screen.getByText(/Hiển thị 21-40 trong tổng số 100 phim/)).toBeInTheDocument();
  });

  test('disables prev button on first page', () => {
    render(
      <Pagination
        currentPage={1}
        totalPages={5}
        onPageChange={mockOnPageChange}
        itemsPerPage={20}
        totalItems={100}
      />
    );

    const prevButton = screen.getByTitle('Trang trước');
    expect(prevButton).toBeDisabled();
  });

  test('disables next button on last page', () => {
    render(
      <Pagination
        currentPage={5}
        totalPages={5}
        onPageChange={mockOnPageChange}
        itemsPerPage={20}
        totalItems={100}
      />
    );

    const nextButton = screen.getByTitle('Trang sau');
    expect(nextButton).toBeDisabled();
  });

  test('does not render when totalPages is 1', () => {
    const { container } = render(
      <Pagination
        currentPage={1}
        totalPages={1}
        onPageChange={mockOnPageChange}
        itemsPerPage={20}
        totalItems={20}
      />
    );

    expect(container.firstChild).toBeNull();
  });
});

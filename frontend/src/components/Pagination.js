import React from 'react';
import './Pagination.css';

/**
 * Pagination Component
 * Handles pagination controls with page numbers and navigation
 */
const Pagination = ({ currentPage, totalPages, onPageChange, itemsPerPage, totalItems }) => {
  if (totalPages <= 1) return null;

  const maxVisiblePages = 5;
  let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
  let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

  // Adjust if we're near the end
  if (endPage - startPage < maxVisiblePages - 1) {
    startPage = Math.max(1, endPage - maxVisiblePages + 1);
  }

  const pages = [];
  for (let i = startPage; i <= endPage; i++) {
    pages.push(i);
  }

  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

  return (
    <div className="pagination-container">
      <div className="pagination-info">
        Hiển thị {startItem}-{endItem} trong tổng số {totalItems} phim
      </div>
      
      <div className="pagination">
        <button
          className="pagination-btn"
          onClick={() => onPageChange(1)}
          disabled={currentPage === 1}
          title="Trang đầu"
        >
          ««
        </button>
        
        <button
          className="pagination-btn"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          title="Trang trước"
        >
          «
        </button>

        {startPage > 1 && (
          <>
            <button
              className="pagination-btn"
              onClick={() => onPageChange(1)}
            >
              1
            </button>
            {startPage > 2 && <span className="pagination-ellipsis">...</span>}
          </>
        )}

        {pages.map(page => (
          <button
            key={page}
            className={`pagination-btn ${currentPage === page ? 'active' : ''}`}
            onClick={() => onPageChange(page)}
          >
            {page}
          </button>
        ))}

        {endPage < totalPages && (
          <>
            {endPage < totalPages - 1 && <span className="pagination-ellipsis">...</span>}
            <button
              className="pagination-btn"
              onClick={() => onPageChange(totalPages)}
            >
              {totalPages}
            </button>
          </>
        )}

        <button
          className="pagination-btn"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          title="Trang sau"
        >
          »
        </button>
        
        <button
          className="pagination-btn"
          onClick={() => onPageChange(totalPages)}
          disabled={currentPage === totalPages}
          title="Trang cuối"
        >
          »»
        </button>
      </div>
    </div>
  );
};

export default Pagination;

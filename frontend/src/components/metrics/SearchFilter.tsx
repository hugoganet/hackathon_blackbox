import React from 'react';
import { Search, Filter } from 'lucide-react';

interface SearchFilterProps {
  searchTerm: string;
  onSearchChange: (term: string) => void;
  placeholder?: string;
}

const SearchFilter: React.FC<SearchFilterProps> = ({
  searchTerm,
  onSearchChange,
  placeholder = "Search..."
}) => {
  return (
    <div className="flex items-center space-x-4">
      {/* Search Input */}
      <div className="relative flex-1 max-w-md">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-4 w-4 text-gray-400" />
        </div>
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          placeholder={placeholder}
        />
        {searchTerm && (
          <button
            onClick={() => onSearchChange('')}
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
          >
            <span className="text-gray-400 hover:text-gray-600 text-sm">✕</span>
          </button>
        )}
      </div>

      {/* Filter Button (placeholder for future functionality) */}
      <button className="flex items-center px-3 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors duration-200">
        <Filter className="h-4 w-4 mr-2" />
        <span className="text-sm font-medium">Filter</span>
      </button>
    </div>
  );
};

export default SearchFilter;

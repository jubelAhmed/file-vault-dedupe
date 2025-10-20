import React, { useState, useEffect } from 'react';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { fileService } from '../services/fileService';

export interface SearchFilters extends Record<string, string> {
  search: string;
  file_type: string;
  min_size: string;
  max_size: string;
  start: string;
  end: string;
}

interface FileSearchFilterProps {
  onSearch: (filters: SearchFilters) => void;
  isLoading?: boolean;
}

export const FileSearchFilter: React.FC<FileSearchFilterProps> = ({
  onSearch,
  isLoading = false
}) => {
  const [filters, setFilters] = useState<SearchFilters>({
    search: '',
    file_type: '',
    min_size: '',
    max_size: '',
    start: '',
    end: ''
  });

  const [availableFileTypes, setAvailableFileTypes] = useState<string[]>([]);
  const [isLoadingFileTypes, setIsLoadingFileTypes] = useState(false);

  // Load available file types on component mount
  useEffect(() => {
    const loadFileTypes = async () => {
      setIsLoadingFileTypes(true);
      try {
        const response = await fileService.getFileTypes();
        setAvailableFileTypes(response.file_types || []);
      } catch (error) {
        console.error('Failed to load file types:', error);
        setAvailableFileTypes([]);
      } finally {
        setIsLoadingFileTypes(false);
      }
    };

    loadFileTypes();
  }, []);

  const handleFilterChange = (field: keyof SearchFilters, value: string) => {
    const newFilters = { ...filters, [field]: value };
    setFilters(newFilters);
  };

  const handleSearch = () => {
    onSearch(filters);
  };

  const handleClearFilters = () => {
    const clearedFilters: SearchFilters = {
      search: '',
      file_type: '',
      min_size: '',
      max_size: '',
      start: '',
      end: ''
    };
    setFilters(clearedFilters);
    onSearch(clearedFilters);
  };

  const hasActiveFilters = Object.values(filters).some(value => value.trim() !== '');

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Search & Filter Files</h3>
        {hasActiveFilters && (
          <button
            onClick={handleClearFilters}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <XMarkIcon className="h-4 w-4 mr-1" />
            Clear All
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
        {/* Search Field */}
        <div>
          <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
            Search Filename
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              id="search"
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              placeholder="Enter filename to search..."
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
        </div>

        {/* File Type Dropdown */}
        <div>
          <label htmlFor="file_type" className="block text-sm font-medium text-gray-700 mb-1">
            File Type
          </label>
          <select
            id="file_type"
            value={filters.file_type}
            onChange={(e) => handleFilterChange('file_type', e.target.value)}
            disabled={isLoadingFileTypes}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md leading-5 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm disabled:bg-gray-50 disabled:text-gray-500"
          >
            <option value="">All file types</option>
            {availableFileTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
          {isLoadingFileTypes && (
            <p className="mt-1 text-xs text-gray-500">Loading file types...</p>
          )}
        </div>

        {/* Min Size */}
        <div>
          <label htmlFor="min_size" className="block text-sm font-medium text-gray-700 mb-1">
            Min Size (MB)
          </label>
          <select
            id="min_size"
            value={filters.min_size}
            onChange={(e) => handleFilterChange('min_size', e.target.value)}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md leading-5 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            <option value="">No minimum</option>
            <option value="1024">1 KB</option>
            <option value="5120">5 KB</option>
            <option value="10240">10 KB</option>
            <option value="51200">50 KB</option>
            <option value="102400">100 KB</option>
            <option value="512000">500 KB</option>
            <option value="1048576">1 MB</option>
            <option value="5242880">5 MB</option>
            <option value="10485760">10 MB</option>
          </select>
        </div>

        {/* Max Size */}
        <div>
          <label htmlFor="max_size" className="block text-sm font-medium text-gray-700 mb-1">
            Max Size (MB)
          </label>
          <select
            id="max_size"
            value={filters.max_size}
            onChange={(e) => handleFilterChange('max_size', e.target.value)}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md leading-5 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            <option value="">No maximum</option>
            <option value="1024">1 KB</option>
            <option value="5120">5 KB</option>
            <option value="10240">10 KB</option>
            <option value="51200">50 KB</option>
            <option value="102400">100 KB</option>
            <option value="512000">500 KB</option>
            <option value="1048576">1 MB</option>
            <option value="5242880">5 MB</option>
            <option value="10485760">10 MB</option>
          </select>
        </div>

        {/* Start Date */}
        <div>
          <label htmlFor="start" className="block text-sm font-medium text-gray-700 mb-1">
            Uploaded Start Date
          </label>
          <input
            type="date"
            id="start"
            value={filters.start}
            onChange={(e) => handleFilterChange('start', e.target.value)}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md leading-5 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
        </div>

        {/* End Date */}
        <div>
          <label htmlFor="end" className="block text-sm font-medium text-gray-700 mb-1">
            Uploaded End Date
          </label>
          <input
            type="date"
            id="end"
            value={filters.end}
            onChange={(e) => handleFilterChange('end', e.target.value)}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md leading-5 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
        </div>
      </div>

      {/* Search Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSearch}
          disabled={isLoading}
          className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Searching...
            </>
          ) : (
            <>
              <MagnifyingGlassIcon className="h-4 w-4 mr-2" />
              Search Files
            </>
          )}
        </button>
      </div>
    </div>
  );
};

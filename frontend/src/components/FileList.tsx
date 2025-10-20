import React, { useCallback, useState } from 'react';
import { fileService } from '../services/fileService';
import { DocumentIcon, TrashIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useUserId } from '../contexts/UserIdContext';
import { FileSearchFilter, SearchFilters } from './FileSearchFilter';

export const FileList: React.FC = () => {
  const queryClient = useQueryClient();
  const { userId } = useUserId();
  const [isSearching, setIsSearching] = useState(false);

  // Debug: Log userId changes
  React.useEffect(() => {
    console.log('FileList: userId changed to:', userId);
  }, [userId]);

  // Query for fetching files (without search filters initially)
  const { data: files, isLoading, error } = useQuery({
    queryKey: ['files', userId],
    queryFn: async () => {
      console.log('FileList: Fetching files for userId:', userId);
      return fileService.getFiles();
    },
    enabled: !!userId, // Only run query when userId is available
  });

  // Format file size to human-readable format
  const formatFileSize = useCallback((bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }, []);

  // Mutation for deleting files
  const deleteMutation = useMutation({
    mutationFn: fileService.deleteFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files', userId] });
      // Invalidate and refetch stats queries to update the StatsPanel
      queryClient.invalidateQueries({ queryKey: ['storageStats', userId] });
      queryClient.invalidateQueries({ queryKey: ['deduplicationStats', userId] });
    },
  });

  // Mutation for downloading files
  const downloadMutation = useMutation({
    mutationFn: ({ fileUrl, filename }: { fileUrl: string; filename: string }) =>
      fileService.downloadFile(fileUrl, filename),
  });

  const handleDelete = async (id: string) => {
    try {
      await deleteMutation.mutateAsync(id);
    } catch (err) {
      console.error('Delete error:', err);
    }
  };

  const handleDownload = async (fileUrl: string, filename: string) => {
    try {
      await downloadMutation.mutateAsync({ fileUrl, filename });
    } catch (err) {
      console.error('Download error:', err);
    }
  };

  const handleSearch = async (filters: SearchFilters) => {
    setIsSearching(true);
    try {
      console.log('FileList: Searching with filters:', filters);
      const filteredFiles = await fileService.getFiles(filters);
      // Update the query cache with the filtered results
      queryClient.setQueryData(['files', userId], filteredFiles);
    } catch (err) {
      console.error('Search error:', err);
    } finally {
      setIsSearching(false);
    }
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Uploaded Files</h2>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Loading files...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Uploaded Files</h2>
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading files</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{String(error)}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Uploaded Files</h2>
      
      {/* Search Filter Component */}
      <FileSearchFilter
        onSearch={handleSearch}
        isLoading={isSearching}
      />
      
      <div className="mt-6 flow-root">
          <ul className="-my-5 divide-y divide-gray-200">
            { files && files.length > 0 ? files.map((file) => (
              <li key={file.id} className="py-4">
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    <DocumentIcon className="h-8 w-8 text-gray-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {file.original_filename}
                    </p>
                    <p className="text-sm text-gray-500">
                      {file.file_type} • {formatFileSize(file.size)}
                      
                    </p>
                    <p className="text-sm text-gray-500">
                      Uploaded {new Date(file.uploaded_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleDownload(file.file_url || file.file, file.original_filename)}
                      disabled={downloadMutation.isPending}
                      className="inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                      Download
                    </button>
                    <button
                      onClick={() => handleDelete(file.id)}
                      disabled={deleteMutation.isPending}
                      className="inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                    >
                      <TrashIcon className="h-4 w-4 mr-1" />
                      Delete
                    </button>
                  </div>
                </div>
              </li>
            ))
          : (
            <li className="py-8">
              <div className="text-center">
                <DocumentIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No files uploaded</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Get started by uploading your first file.
                </p>
              </div>
            </li>
          )}
          </ul>
        </div>
    </div>
  );
}; 
import React from 'react';
import { fileService } from '../services/fileService';
import { useUserId } from '../contexts/UserIdContext';
import { useQuery } from '@tanstack/react-query';

const StatsPanel: React.FC = () => {
  const { userId, isAuthenticated } = useUserId();

  // Query for storage stats
  const { data: storageStats, isLoading: storageLoading, error: storageError } = useQuery({
    queryKey: ['storageStats', userId],
    queryFn: fileService.getStorageStats,
    enabled: !!isAuthenticated && !!userId,
  });

  // Query for deduplication stats
  const { data: deduplicationStats, isLoading: deduplicationLoading, error: deduplicationError } = useQuery({
    queryKey: ['deduplicationStats', userId],
    queryFn: fileService.getDeduplicationStats,
    enabled: !!isAuthenticated && !!userId,
  });

  const loading = storageLoading || deduplicationLoading;
  const error = storageError || deduplicationError;

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatPercentage = (value: number): string => {
    return value.toFixed(1) + '%';
  };

  if (!isAuthenticated) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">Statistics</h3>
        <p className="text-gray-500">Please set a User ID to view statistics.</p>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Statistics</h3>
        {loading && (
          <div className="text-sm text-gray-500">Loading...</div>
        )}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {String(error)}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* User Storage Usage */}
        <div className="border rounded-lg p-4">
          <h4 className="font-semibold text-gray-800 mb-3">Your Storage Usage</h4>
          {storageStats ? (
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Used</span>
                <span className="font-mono">{formatBytes(storageStats.original_storage_used)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Quota</span>
                <span className="font-mono">{formatBytes(storageStats.quota_limit)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Remaining</span>
                <span className="font-mono">{formatBytes(storageStats.quota_remaining)}</span>
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-600">Usage</span>
                  <span className="font-mono">{formatPercentage(storageStats.quota_usage_percentage)}</span>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded">
                  <div
                    className="h-2 bg-blue-500 rounded"
                    style={{ width: `${Math.min(Math.max(storageStats.quota_usage_percentage, 0), 100)}%` }}
                  />
                </div>
              </div>
            </div>
          ) : (
            <p className="text-gray-500">Loading storage stats...</p>
          )}
        </div>

        {/* System Deduplication */}
        <div className="border rounded-lg p-4">
          <h4 className="font-semibold text-gray-800 mb-3">System Deduplication</h4>
          {deduplicationStats ? (
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Total Files</span>
                <span className="font-mono">{deduplicationStats.total_files}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Original Files</span>
                <span className="font-mono">{deduplicationStats.original_files}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">References</span>
                <span className="font-mono">{deduplicationStats.reference_files}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Dedup Ratio</span>
                <span className="font-mono">{formatPercentage(deduplicationStats.deduplication_ratio * 100)}</span>
              </div>
              <div className="pt-2 border-t">
                <div className="flex justify-between">
                  <span className="text-gray-600">System Savings</span>
                  <span className="font-mono text-green-600">{formatBytes(deduplicationStats.storage_savings)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Savings %</span>
                  <span className="font-mono text-green-600">{formatPercentage(deduplicationStats.savings_percentage)}</span>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-gray-500">Loading system stats...</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default StatsPanel;

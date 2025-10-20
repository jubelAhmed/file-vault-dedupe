import React, { useState } from 'react';
import { useUserId } from '../contexts/UserIdContext';

const UserIdSelector: React.FC = () => {
  const { userId, setUserId, clearUserId } = useUserId();
  const [inputValue, setInputValue] = useState(userId || '');
  const [isEditing, setIsEditing] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      console.log('UserIdSelector: Setting userId to:', inputValue.trim());
      setUserId(inputValue.trim());
      setIsEditing(false);
    }
  };

  const handleClear = () => {
    clearUserId();
    setInputValue('');
    setIsEditing(false);
  };

  const handleEdit = () => {
    setIsEditing(true);
    setInputValue(userId || '');
  };

  const handleCancel = () => {
    setIsEditing(false);
    setInputValue(userId || '');
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow-md mb-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-3">User ID</h3>
      
      {!isEditing ? (
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-sm text-gray-600">Current User:</span>
            <span className="font-mono bg-gray-100 px-3 py-1 rounded text-sm">
              {userId || 'Not set'}
            </span>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={handleEdit}
              className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
            >
              Change
            </button>
            {userId && (
              <button
                onClick={handleClear}
                className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label htmlFor="userId" className="block text-sm font-medium text-gray-700 mb-1">
              Enter User ID
            </label>
            <input
              type="text"
              id="userId"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="e.g., user123, john_doe, test-user"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              autoFocus
            />
            <p className="text-xs text-gray-500 mt-1">
              3-50 characters, letters, numbers, underscores, and hyphens only
            </p>
          </div>
          <div className="flex space-x-2">
            <button
              type="submit"
              disabled={!inputValue.trim()}
              className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              Save
            </button>
            <button
              type="button"
              onClick={handleCancel}
              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default UserIdSelector;

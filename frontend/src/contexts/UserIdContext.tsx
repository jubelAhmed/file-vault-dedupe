import React, { createContext, useContext, useState, useEffect, ReactNode, useMemo, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { setUserId, getUserId, clearUserId } from '../services/fileService';
import { API_CONFIG } from '../config/api';

interface UserIdContextType {
  userId: string | null;
  setUserId: (userId: string) => void;
  clearUserId: () => void;
  isAuthenticated: boolean;
}

const UserIdContext = createContext<UserIdContextType | undefined>(undefined);

interface UserIdProviderProps {
  children: ReactNode;
}

export const UserIdProvider: React.FC<UserIdProviderProps> = ({ children }) => {
  const queryClient = useQueryClient();
  const [userId, setUserIdState] = useState<string | null>(() => {
    // Initialize from localStorage or default
    return localStorage.getItem('userId') || API_CONFIG.DEFAULT_USER_ID;
  });

  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

  // Update authentication status when userId changes
  useEffect(() => {
    setIsAuthenticated(!!userId);
  }, [userId]);

  // Set UserId in both context and service
  const handleSetUserId = useCallback((newUserId: string) => {
    setUserIdState(newUserId);
    setUserId(newUserId);
    localStorage.setItem('userId', newUserId);
  }, []);

  // Clear UserId from both context and service
  const handleClearUserId = useCallback(() => {
    setUserIdState(null);
    clearUserId();
    localStorage.removeItem('userId');
  }, []);

  // Initialize service with current userId
  useEffect(() => {
    if (userId) {
      setUserId(userId);
    }
  }, [userId]);

  // Invalidate all queries when userId changes to refetch data for new user
  useEffect(() => {
    console.log('UserIdContext: Invalidating queries for userId:', userId);
    queryClient.invalidateQueries();
  }, [userId, queryClient]);

  const value: UserIdContextType = useMemo(() => ({
    userId,
    setUserId: handleSetUserId,
    clearUserId: handleClearUserId,
    isAuthenticated,
  }), [userId, handleSetUserId, handleClearUserId, isAuthenticated]);

  return (
    <UserIdContext.Provider value={value}>
      {children}
    </UserIdContext.Provider>
  );
};

export const useUserId = (): UserIdContextType => {
  const context = useContext(UserIdContext);
  if (context === undefined) {
    throw new Error('useUserId must be used within a UserIdProvider');
  }
  return context;
};

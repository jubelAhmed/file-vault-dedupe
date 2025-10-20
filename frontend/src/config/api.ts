// API Configuration
export const API_CONFIG = {
  // Default API URL - can be overridden by environment variable
  BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  
  // Timeout for API requests (30 seconds)
  TIMEOUT: 30000,
  
  // Default UserId for testing
  DEFAULT_USER_ID: 'test-user',
};

// Helper function to get the full API URL
export const getApiUrl = (endpoint: string = ''): string => {
  const baseUrl = API_CONFIG.BASE_URL.endsWith('/') 
    ? API_CONFIG.BASE_URL.slice(0, -1) 
    : API_CONFIG.BASE_URL;
  
  const cleanEndpoint = endpoint.startsWith('/') 
    ? endpoint 
    : `/${endpoint}`;
  
  return `${baseUrl}${cleanEndpoint}`;
};

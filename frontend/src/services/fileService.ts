import axios from 'axios';
import { File as FileType } from '../types/file';
import { API_CONFIG } from '../config/api';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
});

// Global UserId management
let currentUserId: string | null = null;

// Set UserId for all requests
export const setUserId = (userId: string) => {
  currentUserId = userId;
  apiClient.defaults.headers.common['UserId'] = userId;
};

// Get current UserId
export const getUserId = (): string | null => {
  return currentUserId;
};

// Clear UserId
export const clearUserId = () => {
  currentUserId = null;
  delete apiClient.defaults.headers.common['UserId'];
};

// Request interceptor to ensure UserId is always set
apiClient.interceptors.request.use(
  (config) => {
    if (!config.headers['UserId'] && currentUserId) {
      config.headers['UserId'] = currentUserId;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle UserId validation errors
      console.error('UserId validation failed:', error.response.data);
    } else if (error.response?.status === 429) {
      // Handle rate limiting
      console.error('Rate limit exceeded:', error.response.data);
    }
    return Promise.reject(error);
  }
);

// Do not force DEFAULT_USER_ID here; UserIdContext initializes and sets it.

export const fileService = {
  async uploadFile(file: File): Promise<FileType> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post('/files/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async getFiles(searchParams?: Record<string, string>): Promise<FileType[]> {
    const params = new URLSearchParams();
    
    // Add search parameters if provided
    if (searchParams) {
      Object.entries(searchParams).forEach(([key, value]) => {
        if (value && value.trim() !== '') {
          params.append(key, value);
        }
      });
    }
    
    const queryString = params.toString();
    const url = queryString ? `/files/?${queryString}` : '/files/';
    
    const response = await apiClient.get(url);
    return response.data.results || [];
  },

  async deleteFile(id: string): Promise<void> {
    await apiClient.delete(`/files/${id}/`);
  },

  async downloadFile(fileUrl: string, filename: string): Promise<void> {
    try {
      const response = await apiClient.get(fileUrl, {
        responseType: 'blob',
      });
      
      // Create a blob URL and trigger download
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download error:', error);
      throw new Error('Failed to download file');
    }
  },

  // Additional service methods for new API endpoints
  async getStorageStats(): Promise<any> {
    const response = await apiClient.get('/files/storage_stats/');
    return response.data;
  },

  async getDeduplicationStats(): Promise<any> {
    const response = await apiClient.get('/files/deduplication_stats/');
    return response.data;
  },

  async getFileTypes(): Promise<any> {
    const response = await apiClient.get('/files/file_types/');
    return response.data;
  },

  async getFileById(id: string): Promise<FileType> {
    const response = await apiClient.get(`/files/${id}/`);
    return response.data;
  },
}; 
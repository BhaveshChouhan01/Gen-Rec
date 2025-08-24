import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API service functions
export const apiService = {
  // Test connection
  async testConnection() {
    try {
      const response = await axios.get(`${API_BASE_URL}/`);
      return response.data;
    } catch (error) {
      throw new Error('Cannot connect to backend');
    }
  },

  // Search images (adjust endpoint to match your backend)
  async searchImages(query, perPage = 9) {
    try {
      const response = await api.get('/search-images', {
        params: { query, per_page: perPage }
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Search failed');
    }
  },

  // Analyze uploaded image
  async analyzeUploadedImage(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await api.post('/analyze-image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000,
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Analysis failed');
    }
  },

  // Analyze image from URL
  async analyzeImageUrl(url) {
    try {
      const response = await api.get('/analyze-url', {
        params: { url }
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'URL analysis failed');
    }
  }
};

export default apiService;
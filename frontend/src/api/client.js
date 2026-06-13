import axios from 'axios';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

// Intercept responses — surface detail/code from backend errors
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.detail || error.message || 'An unexpected error occurred.';
    const code = error.response?.data?.code || 'UNKNOWN_ERROR';
    const enhanced = new Error(detail);
    enhanced.code = code;
    enhanced.status = error.response?.status;
    return Promise.reject(enhanced);
  }
);

export default client;

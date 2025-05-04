import axios from 'axios';

// Configure axios with the backend API URL
const apiInstance = axios.create({
  baseURL: 'https://koshimart-api-6973a89b9858.herokuapp.com',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add response interceptor to handle errors
apiInstance.interceptors.response.use(
  response => response,
  error => {
    // Log errors for debugging
    console.error('API Error:', error.response ? error.response.data : error.message);
    return Promise.reject(error);
  }
);

export default apiInstance; 
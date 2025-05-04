import axios from "axios";
import { BASE_URL } from "./constants";

// Create custom axios instance
const apiInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
  // Enable credentials to ensure cookies are sent with requests
  withCredentials: false,
});

// Request interceptor for API calls
apiInstance.interceptors.request.use(
  (config) => {
    // You can add authorization headers here if needed
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers['Authorization'] = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    console.error("Request error:", error);
    return Promise.reject(error);
  }
);

// Response interceptor for API calls
apiInstance.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // If the error is due to a timeout, retry up to 2 times
    if (error.code === "ECONNABORTED" && !originalRequest._retry) {
      originalRequest._retry = (originalRequest._retry || 0) + 1;
      if (originalRequest._retry < 3) {
        console.log(`Request timed out, retrying (${originalRequest._retry}/3)...`);
        return apiInstance(originalRequest);
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiInstance; 
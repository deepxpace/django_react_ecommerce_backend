import apiInstance from "./axios";

/**
 * Safely fetches reviews for a product, handles undefined IDs gracefully
 * @param {number|string|undefined} productId - The product ID
 * @returns {Promise<Array>} - Array of reviews or empty array
 */
export const safelyFetchReviews = async (productId) => {
  if (!productId || productId === "undefined") {
    console.warn("Invalid product ID:", productId);
    return [];
  }
  try {
    const response = await apiInstance.get(`reviews/${productId}/`);
    return response.data || [];
  } catch (error) {
    console.error("Error fetching reviews:", error);
    return [];
  }
};

/**
 * Safely submits a product review, handles undefined IDs gracefully
 * @param {number|string|undefined} productId - The product ID
 * @param {Object} reviewData - The review data to submit
 * @returns {Promise<Object>} - Response data or empty object
 */
export const safelySubmitReview = async (productId, reviewData) => {
  if (!productId || productId === "undefined") {
    console.warn("Attempted to submit review with invalid product ID:", productId);
    return { success: false, message: "Invalid product ID" };
  }

  try {
    const formData = new FormData();
    Object.keys(reviewData).forEach(key => {
      formData.append(key, reviewData[key]);
    });
    
    const response = await apiInstance.post(`reviews/${productId}/`, formData);
    return response.data || { success: true };
  } catch (error) {
    console.error("Error submitting review:", error);
    return { success: false, message: "Error submitting review" };
  }
};

/**
 * Fetch products from the API
 * @returns {Promise<Array>} - Array of products or empty array
 */
export const fetchProducts = async () => {
  try {
    console.log("Fetching products from API...");
    const response = await apiInstance.get("products/");
    console.log("Products fetched:", response.data);
    return response.data || [];
  } catch (error) {
    console.error("Error fetching products:", error);
    return [];
  }
};

/**
 * Fetch a single product by slug
 * @param {string} slug - The product slug
 * @returns {Promise<Object>} - Product object or null
 */
export const fetchProductBySlug = async (slug) => {
  if (!slug) {
    console.warn("Attempted to fetch product with invalid slug");
    return null;
  }

  try {
    const response = await apiInstance.get(`products/${slug}/`);
    return response.data || null;
  } catch (error) {
    console.error("Error fetching product:", error);
    return null;
  }
}; 
import React, { useEffect, useState } from 'react';
import apiInstance from '../../services/apiInstance';
import { safelyFetchReviews, safelySubmitReview } from "../../utils/apiHelpers";

const ProductDetail = () => {
  const [product, setProduct] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [createReview, setCreateReview] = useState({
    rating: 0,
    review: '',
  });
  const [userData, setUserData] = useState(null);

  const fetchReviewData = async () => {
    if (product) {
      const reviewsData = await safelyFetchReviews(product.id);
      setReviews(reviewsData);
    }
  };

  useEffect(() => {
    fetchReviewData();
  }, [product]);

  const handleReviewSubmit = (e) => {
    e.preventDefault();

    const reviewData = {
      user_id: userData?.user_id,
      product_id: product?.id,
      rating: createReview.rating,
      review: createReview.review,
    };

    safelySubmitReview(product?.id, reviewData).then(() => {
      fetchReviewData();
    });
  };

  return (
    <div>
      {/* Render your component content here */}
    </div>
  );
};

export default ProductDetail; 
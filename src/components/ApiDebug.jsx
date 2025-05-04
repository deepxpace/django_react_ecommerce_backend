import { useState, useEffect } from 'react';
import apiInstance from '../utils/axios';

function ApiDebug() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        console.log('Fetching products...');
        const response = await apiInstance.get('products/');
        console.log('API response:', response);
        setProducts(response.data || []);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching products:', error);
        setError(error.message || 'Error fetching products');
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

  return (
    <div className="container mt-5">
      <h2>API Debug</h2>
      {loading && <p>Loading products...</p>}
      {error && (
        <div className="alert alert-danger">
          <strong>Error:</strong> {error}
        </div>
      )}
      {!loading && !error && products.length === 0 && (
        <div className="alert alert-warning">No products found</div>
      )}
      {products.length > 0 && (
        <div>
          <p>Found {products.length} products:</p>
          <ul className="list-group">
            {products.map(product => (
              <li key={product.id} className="list-group-item">
                <strong>{product.title}</strong> - ${product.price}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default ApiDebug; 
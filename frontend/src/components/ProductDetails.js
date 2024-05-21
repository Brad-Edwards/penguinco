import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import ProductTile from './ProductTile';
import CustomerInfo from './CustomerInfo';
import axios from 'axios';

function ProductDetails() {
  const location = useLocation();
  const { productId } = location.state || {};
  const [productDetails, setProductDetails] = useState(null);

  useEffect(() => {
    if (productId) {
      axios.get(`${process.env.REACT_APP_API_URL}/api/product_details`, {
        params: { productId }
      })
      .then(response => {
        const product = {
          ...response.data.product,
          prices: { data: response.data.prices }
        };
        setProductDetails(product);
      })
      .catch(error => console.error('Error:', error));
    }
  }, [productId]);

  return (
    <div className="product-details-container">
      {productDetails && <ProductTile product={productDetails} className="product-details-tile" />}
      {productDetails && <CustomerInfo productDetails={productDetails} />}
    </div>
  );
}

export default ProductDetails;
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import ProductTile from './ProductTile';

function Landing() {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    axios.get(`${process.env.REACT_APP_API_URL}/api/products`)
      .then(response => {
        const productsArray = Object.values(response.data).map(item => ({
          ...item.product,
          prices: item.prices
        }));
        setProducts(productsArray);
      })
      .catch(error => console.error('Error fetching products:', error));
  }, []);

  return (
    <div className="product-grid-container">
      <div className="product-grid">
        {products.map(product => (
          <ProductTile key={product.id} product={product} />
        ))}
      </div>
    </div>
  );
}

export default Landing;

import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Elements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import axios from 'axios';
import ProductTile from './ProductTile';
import PaymentForm from './PaymentForm';

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);

function ProductDetails() {
  const location = useLocation();
  const { productId } = location.state || {};
  const [productDetails, setProductDetails] = useState(null);
  const [clientSecret, setClientSecret] = useState('');

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

        if (response.data.prices && response.data.prices.length > 0) {
          return axios.post(`${process.env.REACT_APP_API_URL}/api/create_payment_intent`, {
            amount: response.data.prices[0].unit_amount,
            currency: 'usd',
            payment_method_types: ['card', 'cashapp', 'us_bank_account'],
          });
        } else {
          throw new Error('No prices available for this product');
        }
      })
      .then(response => {
        setClientSecret(response.data.client_secret);
      })
      .catch(error => console.error('Error:', error));
    }
  }, [productId]);

  const options = { clientSecret };

  return (
    <div className="product-details-container">
      {productDetails && <ProductTile product={productDetails} className="product-details-tile" />}
      {clientSecret && (
        <Elements stripe={stripePromise} options={options}>
          <PaymentForm price={productDetails.prices.data[0].unit_amount / 100} />
        </Elements>
      )}
    </div>
  );
}

export default ProductDetails;

import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Elements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import axios from 'axios';
import PaymentForm from './PaymentForm';

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);

function ProductDetails() {
  const location = useLocation();
  const { productId } = location.state || {};
  const [clientSecret, setClientSecret] = useState('');
  const [productDetails, setProductDetails] = useState(null);

  useEffect(() => {
    if (productId) {
      axios.get(`${process.env.REACT_APP_API_URL}/api/product_details`, {
        params: { productId }
      })
      .then(response => {
        setProductDetails(response.data);
        return axios.post(`${process.env.REACT_APP_API_URL}/api/create_payment_intent`, {
          amount: response.data.price,
          currency: 'usd',
          payment_method_types: ['card', 'cashapp', 'us_bank_account'],
        });
      })
      .then(response => {
        setClientSecret(response.data.client_secret);
      })
      .catch(error => console.error('Error:', error));
    }
  }, [productId]);

  const options = {
    clientSecret: clientSecret,
  };

  return (
    <div>
      <h2>Product Details for Product ID: {productId}</h2>
      {productDetails && (
        <div>
          <p>Product Name: {productDetails.name}</p>
          <p>Price: ${productDetails.price / 100}</p>
        </div>
      )}
      {clientSecret && (
        <Elements stripe={stripePromise} options={options}>
          <PaymentForm />
        </Elements>
      )}
    </div>
  );
}

export default ProductDetails;
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Elements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import axios from 'axios';
import ProductDetails from './components/ProductDetails';
import PaymentForm from './components/PaymentForm';
import SuccessPage from './components/SuccessPage';
import './App.css';

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);

function App() {
  const [clientSecret, setClientSecret] = useState('');

  useEffect(() => {
    axios.post(`${process.env.REACT_APP_API_URL}/api/create_payment_intent`, {
      amount: 1999,
      currency: 'usd',
      payment_method_types: ['card', 'cashapp', 'us_bank_account'],
    })
    .then(response => {
      setClientSecret(response.data.client_secret);
    })
    .catch(error => console.error('Error:', error));
  }, []);

  const options = {
    clientSecret: clientSecret,
  };

  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>PenguinCo</h1>
        </header>
        <Routes>
          <Route path="/" element={
            <>
              <ProductDetails />
              {clientSecret && (
                <Elements stripe={stripePromise} options={options}>
                  <PaymentForm />
                </Elements>
              )}
            </>
          } />
          <Route path="/success" element={<SuccessPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

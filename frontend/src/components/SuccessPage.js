import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useStripe } from '@stripe/react-stripe-js';

function SuccessPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const stripe = useStripe();
  const [paymentStatus, setPaymentStatus] = useState('checking');

  useEffect(() => {
    const clientSecret = new URLSearchParams(location.search).get('payment_intent_client_secret');

    const checkPaymentStatus = async () => {
      if (!clientSecret) {
        console.error('Client secret not found.');
        navigate('/');
        return;
      }

      try {
        const { paymentIntent } = await stripe.retrievePaymentIntent(clientSecret);
        if (paymentIntent.status === 'succeeded') {
          setPaymentStatus('succeeded');
        } else {
          setPaymentStatus('failed');
        }
      } catch (error) {
        console.error('Error retrieving payment intent:', error);
        setPaymentStatus('failed');
      }
    };

    checkPaymentStatus();
  }, [location, navigate, stripe]);

  return (
    <div>
      {paymentStatus === 'checking' && <p>Checking payment status...</p>}
      {paymentStatus === 'succeeded' && <h1>Payment Successful!</h1>}
      {paymentStatus === 'failed' && <h1>Payment Failed</h1>}
    </div>
  );
}

export default SuccessPage;
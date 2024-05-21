import React, { useState, useEffect } from 'react';
import { Elements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import { PaymentElement } from '@stripe/react-stripe-js';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);

function PaymentForm() {
  const navigate = useNavigate();
  const location = useLocation();
  const { customerData, productDetails } = location.state;
  const [clientSecret, setClientSecret] = useState('');

  useEffect(() => {
    const fetchClientSecret = async () => {
      if (clientSecret) return;

      try {
        const customerResponse = await axios.post(`${process.env.REACT_APP_API_URL}/api/get_customer`, customerData);
        const customerId = customerResponse.data.customer_id;

        const paymentIntentResponse = await axios.post(`${process.env.REACT_APP_API_URL}/api/create_payment_intent`, {
          amount: productDetails.prices.data[0].unit_amount,
          currency: 'usd',
          payment_method_types: ['card'],
          customer_id: customerId
        });

        setClientSecret(paymentIntentResponse.data.client_secret);
      } catch (error) {
        console.error('Error fetching client secret:', error);
        navigate('/error');
      }
    };

    fetchClientSecret();
  }, [clientSecret, customerData, productDetails, navigate]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const stripe = await stripePromise;
    const elements = stripe.elements();

    if (!stripe || !elements) {
      return;
    }

    const result = await stripe.confirmPayment({
      elements,
      redirect: 'if_required',
      confirmParams: {
        return_url: `${window.location.origin}/success`,
      },
    });

    if (result.error) {
      console.log(result.error.message);
      navigate('/error');
    } else if (result.paymentIntent && result.paymentIntent.status === 'succeeded') {
      navigate('/success');
    } else {
      navigate('/error');
    }
  };

  return (
    clientSecret && (
      <Elements stripe={stripePromise} options={{ clientSecret }}>
        <form onSubmit={handleSubmit}>
          <PaymentElement />
          <button type="submit">Pay ${productDetails.prices.data[0].unit_amount / 100}</button>
        </form>
      </Elements>
    )
  );
}

export default PaymentForm;

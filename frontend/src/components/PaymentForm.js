import React, { useState } from 'react';
import { useStripe, useElements, PaymentElement } from '@stripe/react-stripe-js';
import { useNavigate } from 'react-router-dom';

function PaymentForm() {
  const stripe = useStripe();
  const elements = useElements();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!stripe || !elements) {
      return;
    }

    setLoading(true);
    const result = await stripe.confirmPayment({
      elements,
      redirect: 'if_required',
      confirmParams: {
        return_url: `${window.location.origin}/payment-complete`,
      },
    });

    setLoading(false);
    if (result.error) {
      console.log(result.error.message);
      navigate('/error');
    } else if (result.paymentIntent) {
      console.log(result.paymentIntent.payment_method_types)
      if (result.paymentIntent.payment_method_types.includes('us_bank_account')) {
        setTimeout(() => {
          navigate('/success');
        }, 1000);
      } else {
        if (result.paymentIntent.status === 'succeeded') {
          navigate('/success');
        } else {
          navigate('/error');
        }
      }
    }
  };

  return (
    <form className='payment-form-container' onSubmit={handleSubmit}>
      <PaymentElement />
      <button type="submit" disabled={!stripe || loading}>Pay $19.99</button>
      {loading && <p>Processing... Please wait.</p>}
    </form>
  );
}

export default PaymentForm;

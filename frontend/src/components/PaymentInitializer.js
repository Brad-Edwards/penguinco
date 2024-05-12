import React, { useEffect, useContext } from 'react';
import axios from 'axios';
import { ClientSecretContext } from './ClientSecretProvider';
function PaymentInitializer() {
  const { setClientSecret } = useContext(ClientSecretContext);

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
  }, [setClientSecret]);

  return null;
}

export default PaymentInitializer;


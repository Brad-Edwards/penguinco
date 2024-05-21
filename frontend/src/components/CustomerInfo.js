import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function CustomerInfo({ productDetails }) {
  const navigate = useNavigate();
  const [customerData, setCustomerData] = useState({
    name: '',
    email: '',
    address: ''
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setCustomerData({ ...customerData, [name]: value });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      navigate('/payment', { state: { customerData, productDetails } });
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="text" name="name" placeholder="Name" value={customerData.name} onChange={handleInputChange} required />
      <input type="email" name="email" placeholder="Email" value={customerData.email} onChange={handleInputChange} required />
      <input type="text" name="address" placeholder="Address" value={customerData.address} onChange={handleInputChange} required />
      <button type="submit">Proceed to Payment</button>
    </form>
  );
}

export default CustomerInfo;



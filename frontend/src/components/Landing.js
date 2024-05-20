import React from 'react';
import { useNavigate } from 'react-router-dom';

function Landing() {
  const navigate = useNavigate();

  const handlePurchase = (productId) => {
    navigate('/purchase', { state: { productId } });
  };

  return (
    <div>
      <button onClick={() => handlePurchase(1)}>Buy Product 1</button>
      <button onClick={() => handlePurchase(2)}>Buy Product 2</button>
    </div>
  );
}

export default Landing;
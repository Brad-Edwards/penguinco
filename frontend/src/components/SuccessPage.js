import React from 'react';
import { useNavigate } from 'react-router-dom';

function SuccessPage() {
  const navigate = useNavigate();

  const handleGoHome = () => {
    navigate('/');
  };

  return (
    <div className="success-page">
      <h1>Payment Successful!</h1>
      <p>Thank you for your purchase.</p>
      <button onClick={handleGoHome}>Go to Home</button>
    </div>
  );
}

export default SuccessPage;


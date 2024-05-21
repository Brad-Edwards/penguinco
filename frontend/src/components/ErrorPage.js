import React from 'react';
import { useNavigate } from 'react-router-dom';

function ErrorPage() {
  const navigate = useNavigate();

  const handleGoHome = () => {
    navigate('/');
  };

  return (
    <div className="error-page">
      <h1>Payment was not successful!</h1>
      <p>Please try again.</p>
      <button onClick={handleGoHome}>Go to Home</button>
    </div>
  );
}

export default ErrorPage;


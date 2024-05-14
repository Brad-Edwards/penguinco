import React from 'react';
import plushieImage from '../assets/penguin-plushie.jpg'; 

function ProductDetails() {
  return (
    <div className="product-details">
      <img src={plushieImage} alt="Penguin Plushie" />
      <h2>Penguin Plushie</h2>
      <p>Adorable penguin plushie to keep you company during those cold winter nights.</p>
      <p>Price: $19.99</p>
    </div>
  );
}

export default ProductDetails;


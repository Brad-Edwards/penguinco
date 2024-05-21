import React from 'react';
import { useNavigate } from 'react-router-dom';

function ProductTile({ product }) {
  const { id, name, prices } = product;
  const price = prices?.data?.[0]?.unit_amount / 100;
  const navigate = useNavigate();

  const handleClick = () => {
    navigate('/purchase', { state: { productId: id } });
  };

  return (
    <div className="product-tile" onClick={handleClick}>
      <img src={`images/${id}.jpg`} alt={name} />
      <h2>{name}</h2>
      {price !== undefined ? <p>${price.toFixed(2)}</p> : <p>Price not available</p>}
    </div>
  );
}

export default ProductTile;

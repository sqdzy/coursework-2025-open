import React from 'react';

const ProductImage = ({ image, name }) => {
  return (
    <div className="bg-gray-50 rounded-lg p-4 flex items-center justify-center">
      <img
        src={image}
        alt={name}
        className="max-w-full max-h-96 object-contain"
      />
    </div>
  );
};

export default ProductImage;
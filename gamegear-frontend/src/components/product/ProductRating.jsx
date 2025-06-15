import React from 'react';
import { Star } from 'lucide-react';

const ProductRating = ({ rating }) => {
  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center">
        <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
        <span className="ml-1 font-medium">{rating}</span>
      </div>
      <button className="text-gray-500 text-sm">Отзывы</button>
    </div>
  );
};

export default ProductRating;
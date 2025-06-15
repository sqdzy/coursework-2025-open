import React from 'react';
import { Star } from 'lucide-react';

const StarRating = ({ rating, maxRating = 5, size = 'md', showValue = true }) => {
  const fullStars = Math.floor(rating);
  const hasHalfStar = rating % 1 >= 0.5;

  const sizeClass = {
    sm: "h-4 w-4",
    md: "h-5 w-5",
    lg: "h-6 w-6"
  };

  return (
    <div className="flex items-center">
      <div className="flex">
        {[...Array(fullStars)].map((_, i) => (
          <Star key={`full-${i}`} className={`${sizeClass[size]} fill-yellow-400 text-yellow-400`} />
        ))}

        {hasHalfStar && (
          <div className="relative">
            <Star className={`${sizeClass[size]} text-gray-300`} />
            <div className="absolute inset-0 overflow-hidden w-1/2">
              <Star className={`${sizeClass[size]} fill-yellow-400 text-yellow-400`} />
            </div>
          </div>
        )}

        {[...Array(maxRating - fullStars - (hasHalfStar ? 1 : 0))].map((_, i) => (
          <Star key={`empty-${i}`} className={`${sizeClass[size]} text-gray-300`} />
        ))}
      </div>

      {showValue && (
        <span className="ml-1 font-medium">{rating.toFixed(1)}</span>
      )}
    </div>
  );
};

export default StarRating;
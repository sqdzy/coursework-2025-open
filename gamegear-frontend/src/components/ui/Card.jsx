import React from 'react';

const Card = ({
  children,
  className = '',
  padding = 'p-4',
  shadow = 'shadow-sm',
  rounded = 'rounded-lg',
  ...props
}) => {
  return (
    <div
      className={`bg-white ${padding} ${shadow} ${rounded} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export default Card;
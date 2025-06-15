import React from 'react';

const ProductFeatures = ({ features }) => {
  if (!features || features.length === 0) {
    return null;
  }

  return (
    <ul className="list-disc pl-5 space-y-2">
      {features.map((feature) => (
        <li key={feature.id} className="text-gray-800">
          {feature.feature_name}: {feature.value}
        </li>
      ))}
    </ul>
  );
};

export default ProductFeatures;

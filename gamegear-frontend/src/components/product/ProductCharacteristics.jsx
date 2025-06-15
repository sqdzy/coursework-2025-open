import React from 'react';


const ProductCharacteristics = ({features}) => {

    if (!features || features.length === 0) {


        return null;
    }


    const characteristicsToShow = features.slice(0, 5);

    return (
        <div className="mb-6">
            <h3 className="font-bold text-lg mb-3">Характеристики</h3>
            <ul className="space-y-2">

                {characteristicsToShow.map((feature) => (

                    <li key={feature.id} className="flex text-sm">

                        <div className="text-gray-600 min-w-[120px] md:min-w-[150px] break-words pr-2">
                            {feature.feature_name}:
                        </div>

                        <div className="text-gray-900 font-medium break-words">
                            {feature.value}
                        </div>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default ProductCharacteristics;
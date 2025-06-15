import React from 'react';
import ProductCard from '../product/ProductCard';
import {ArrowRight} from 'lucide-react';
import {Link} from 'react-router-dom';

const PromotionSection = ({promoProducts}) => {
    if (!promoProducts || promoProducts.length === 0) {
        return null;
    }

    return (
        <section className="mb-8 md:mb-12">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl md:text-2xl font-semibold text-gray-800">
                    Акции и спецпредложения
                </h2>
                <Link
                    to="/promotions"
                    className="flex items-center text-sm font-medium text-orange-600 hover:text-orange-700 hover:underline"
                >
                    Все акции
                    <ArrowRight size={16} className="ml-1"/>
                </Link>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 md:gap-6">
                {promoProducts.map((productData) => (

                    <ProductCard
                        key={`promo-${productData.promotion_id || productData.promotion_name}-${productData.id}`}
                        product={productData}/>
                ))}
            </div>

        </section>
    );
};

export default PromotionSection;

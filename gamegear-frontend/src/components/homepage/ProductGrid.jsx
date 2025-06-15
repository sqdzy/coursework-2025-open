import React from 'react';
import ProductCard from '../product/ProductCard';

const ProductGrid = ({products, title = "Наши товары"}) => {
    if (!products || products.length === 0) {
        return null;
    }

    return (
        <section className="mb-8 md:mb-12">

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 md:gap-6">
                {products.map((product) => (
                    <ProductCard key={`latest-${product.id}`} product={product}/>
                ))}
            </div>

        </section>
    );
};

export default ProductGrid;

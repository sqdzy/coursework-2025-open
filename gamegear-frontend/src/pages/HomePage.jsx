import React, {useState, useEffect, useRef} from 'react';
import HomepageBanner from '../components/homepage/HomepageBanner';
import CategoryList from '../components/homepage/CategoryList';
import PromotionSection from '../components/homepage/PromotionSection';
import ProductGrid from '../components/homepage/ProductGrid';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorMessage from '../components/ui/ErrorMessage';
import {fetchHomepageData} from '../services/api';

const HomePage = () => {
    const [homepageData, setHomepageData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const promotionsSectionRef = useRef(null);

    const loadData = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await fetchHomepageData();
            setHomepageData(data);
        } catch (err) {
            setError("Не удалось загрузить данные для главной страницы. Попробуйте обновить.");
            console.error("Homepage fetch error:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const handleSkipToPromotions = (e) => {
        e.preventDefault();
        if (promotionsSectionRef.current) {
            promotionsSectionRef.current.focus()
            promotionsSectionRef.current.scrollIntoView({behavior: 'smooth', block: 'start'});
        }
    };

    return (
        <div className="container mx-auto px-4 py-6">
            <a
                href="#promotions-section"
                onClick={handleSkipToPromotions}
                className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:p-3 focus:bg-white focus:text-orange-600 focus:border focus:border-orange-500 focus:rounded-md focus:shadow-lg"
            >
                Перейти к акциям и предложениям
            </a>

            {loading && <LoadingSpinner text="Загрузка главной страницы..." className="my-16"/>}
            {error && <ErrorMessage message={error} onRetry={loadData} className="my-16"/>}

            {!loading && !error && homepageData && (
                <>
                    <section aria-labelledby="categories-title" className="mb-8 md:mb-12">
                        <CategoryList categories={homepageData.categories}/>
                    </section>

                    {homepageData.banner && (
                        <div className="mb-8 md:mb-12">
                            <HomepageBanner banner={homepageData.banner}/>
                        </div>
                    )}

                    <div id="promotions-section" ref={promotionsSectionRef} tabIndex={-1}
                         className="focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 rounded-sm scroll-mt-16">
                        <PromotionSection promoProducts={homepageData.promotions}/>
                    </div>


                    <section aria-labelledby="latest-products-title" className="mt-8 md:mt-12">
                        <h2 id="latest-products-title" className="text-xl md:text-2xl font-semibold mb-4">Новинки
                            магазина</h2>
                        <ProductGrid products={homepageData.latest_products}/>
                    </section>
                </>
            )}
        </div>
    );
};

export default HomePage;
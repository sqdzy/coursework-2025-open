import React, {useState, useEffect, useCallback} from 'react';
import {useSearchParams} from 'react-router-dom';

import ProductGrid from '../components/homepage/ProductGrid';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorMessage from '../components/ui/ErrorMessage';
import Button from '../components/ui/Button';
import {fetchCatalogProducts} from '../services/api';

const CatalogPage = () => {
    const [searchParams] = useSearchParams();
    const searchQuery = searchParams.get('search');

    const [productsData, setProductsData] = useState({count: 0, next: null, previous: null, results: []});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);


    const loadProducts = useCallback(async (url = null) => {
        setLoading(true);
        setError(null);
        try {

            const data = await fetchCatalogProducts(url, searchQuery);
            setProductsData(data);
        } catch (err) {
            setError(err.message || 'Не удалось загрузить товары.');
            console.error("Catalog/Search page fetch error:", err);

            setProductsData({count: 0, next: null, previous: null, results: []});
        } finally {
            setLoading(false);
        }
    }, [searchQuery]);


    useEffect(() => {
        console.log(`CatalogPage effect: loading products for query "${searchQuery || 'all'}"`);
        loadProducts();

        return () => {
            setProductsData({count: 0, next: null, previous: null, results: []});
            setLoading(true);
            setError(null);
        }
    }, [loadProducts]);


    const handleNextPage = () => {
        if (productsData.next) {
            loadProducts(productsData.next);
        }
    };

    const handlePreviousPage = () => {
        if (productsData.previous) {
            loadProducts(productsData.previous);
        }
    };


    const pageTitle = searchQuery
        ? `Результаты поиска по: "${searchQuery}"`
        : "Каталог товаров";

    return (
        <div className="container mx-auto px-4 py-6">
            <h1 className="text-2xl md:text-3xl font-bold mb-6">{pageTitle}</h1>


            {loading && <LoadingSpinner text="Загрузка товаров..." className="my-16"/>}
            {error && <ErrorMessage message={error} onRetry={() => loadProducts()} className="my-16"/>}

            {!loading && !error && productsData.results.length > 0 && (
                <>

                    <ProductGrid products={productsData.results}
                                 title=""/>


                    <div className="mt-8 flex justify-center items-center gap-4">
                        <Button
                            onClick={handlePreviousPage}
                            disabled={!productsData.previous || loading}
                            variant="outline"
                        >
                            Назад
                        </Button>


                        <Button
                            onClick={handleNextPage}
                            disabled={!productsData.next || loading}
                            variant="outline"
                        >
                            Вперед
                        </Button>
                    </div>
                    <div className="mt-4 text-center text-sm text-gray-500">
                        Показано товаров: {productsData.results.length} из {productsData.count}
                    </div>
                </>
            )}


            {!loading && !error && productsData.results.length === 0 && (
                <div className="text-center py-10 text-gray-500">
                    {searchQuery
                        ? `По запросу "${searchQuery}" ничего не найдено.`
                        : "В каталоге пока нет товаров."
                    }
                </div>
            )}
        </div>
    );
};

export default CatalogPage;

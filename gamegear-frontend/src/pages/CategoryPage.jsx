import React, {useState, useEffect} from 'react';
import {useParams, Link} from 'react-router-dom';


import ProductGrid from '../components/homepage/ProductGrid';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorMessage from '../components/ui/ErrorMessage';
import {fetchCategoryDetail} from '../services/api';

const CategoryPage = () => {
    const {categoryId} = useParams();
    const [categoryData, setCategoryData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadCategoryData = async () => {
        setLoading(true);
        setError(null);
        try {
            console.log(`Fetching data for category ID: ${categoryId}`);
            const data = await fetchCategoryDetail(categoryId);
            setCategoryData(data);
        } catch (err) {
            setError(err.message || `Не удалось загрузить данные для категории ${categoryId}.`);
            console.error(`Category page fetch error for ID ${categoryId}:`, err);
        } finally {
            setLoading(false);
        }
    };


    useEffect(() => {
        if (categoryId) {
            loadCategoryData();
        } else {

            setError("Не указан ID категории.");
            setLoading(false);
        }

        return () => {
            setCategoryData(null);
            setLoading(true);
            setError(null);
        }
    }, [categoryId]);

    return (
        <div className="container mx-auto px-4 py-6">

            <nav className="text-sm mb-4 text-gray-500">
                <Link to="/" className="hover:text-orange-500">Главная</Link>
                <span className="mx-2">/</span>
                {loading && <span>Загрузка категории...</span>}
                {error && <span>Ошибка</span>}
                {categoryData && !error && <span>{categoryData.name}</span>}
            </nav>

            {loading && <LoadingSpinner text={`Загрузка категории ${categoryId}...`} className="my-16"/>}
            {error && <ErrorMessage message={error} onRetry={loadCategoryData} className="my-16"/>}

            {!loading && !error && categoryData && (
                <>

                    <h1 className="text-2xl md:text-3xl font-bold mb-2">{categoryData.name}</h1>

                    {categoryData.description && (
                        <p className="text-gray-600 mb-6">{categoryData.description}</p>
                    )}


                    <ProductGrid
                        products={categoryData.products}
                        title={`Товары в категории "${categoryData.name}"`}
                    />


                    {(!categoryData.products || categoryData.products.length === 0) && (
                        <div className="text-center py-10 text-gray-500">
                            В этой категории пока нет товаров.
                        </div>
                    )}
                </>
            )}

            {!loading && !error && !categoryData && (
                <ErrorMessage message={`Категория с ID ${categoryId} не найдена.`}/>
            )}
        </div>
    );
};

export default CategoryPage;

import React, {useEffect, useState} from 'react';
import Layout from '../components/layout/Layout';
import ProductDetail from '../components/product/ProductDetail';
import {fetchProduct} from '../services/api';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorMessage from '../components/ui/ErrorMessage';


const ProductPage = ({productId}) => {
    const [product, setProduct] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);


    const getProductData = async () => {
        if (!productId) {
            setError('Не указан ID товара.');
            setLoading(false);
            return;
        }
        setLoading(true);
        setError(null);
        try {
            console.log(`Fetching product with ID: ${productId}`);
            const data = await fetchProduct(productId);
            setProduct(data);
        } catch (err) {
            setError(err.message || 'Не удалось загрузить данные о товаре.');
            console.error('Error fetching product:', err);
        } finally {
            setLoading(false);
        }
    };


    useEffect(() => {

        getProductData();


    }, [productId]);


    return (

        <>
            {loading && <LoadingSpinner text="Загрузка товара..."/>}

            {error && <ErrorMessage message={error} onRetry={getProductData}/>}
            {!loading && !error && product && (
                <ProductDetail product={product}/>
            )}
            {!loading && !error && !product && !productId && (
                <ErrorMessage message="Не указан ID товара."/>
            )}
            {!loading && !error && !product && productId && (
                <ErrorMessage message={`Товар с ID ${productId} не найден.`}/>
            )}
        </>
    );

};

export default ProductPage;

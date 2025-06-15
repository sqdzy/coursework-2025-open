import React, { useState, useEffect, useCallback } from 'react';
import ProductImage from './ProductImage';
import ProductCharacteristics from './ProductCharacteristics';
import ProductPrice from './ProductPrice';
import Button from '../ui/Button';
import Modal from '../ui/Modal';
import { Star, RefreshCw } from 'lucide-react';
import ProductReviews from './ProductReviews';
import AddReviewForm from './AddReviewForm';
import { fetchReviews, deleteReview } from '../../services/api';
import { useAuth } from '../context/AuthContext';
import LoadingSpinner from '../ui/LoadingSpinner';
import ErrorMessage from '../ui/ErrorMessage';

const ProductDetail = ({ product }) => {
    const [reviewsData, setReviewsData] = useState({ results: [], count: 0, next: null, previous: null });
    const [reviewsLoading, setReviewsLoading] = useState(false);
    const [reviewsError, setReviewsError] = useState(null);
    const [showReviewForm, setShowReviewForm] = useState(false);
    const [showAllFeaturesModal, setShowAllFeaturesModal] = useState(false);
    const { isAuthenticated, token } = useAuth();
    const [reviewToEdit, setReviewToEdit] = useState(null);

    const loadReviews = useCallback(async (productId, url = null) => {
        if (!productId) return;
        setReviewsLoading(true);
        if (!url) { setReviewsError(null); }
        try {
            const fetchedData = await fetchReviews(productId, url);
            let newResults = [], newCount = 0, newNext = null, newPrevious = null, append = !!url;
            if (typeof fetchedData === 'object' && fetchedData !== null && 'results' in fetchedData && Array.isArray(fetchedData.results)) {
                newResults = fetchedData.results || []; newCount = fetchedData.count || newResults.length; newNext = fetchedData.next || null; newPrevious = fetchedData.previous || null;
            } else if (Array.isArray(fetchedData)) {
                newResults = fetchedData; newCount = fetchedData.length; newNext = null; newPrevious = null; if (append) { append = false; }
            } else { if (!url) { setReviewsData({ results: [], count: 0, next: null, previous: null }); } }
            if (append) { setReviewsData(prevData => ({ count: newCount, next: newNext, previous: newPrevious, results: [...(prevData.results || []), ...newResults.filter(newRev => !(prevData.results || []).some(oldRev => oldRev.id === newRev.id))] }));
            } else { setReviewsData({ results: newResults, count: newCount, next: newNext, previous: newPrevious }); }
        } catch (error) { setReviewsError(error.message || "Не удалось загрузить отзывы."); console.error("[PD] Error loadReviews:", error);
        } finally { setReviewsLoading(false); }
    }, []);

    useEffect(() => {
        const currentProductId = product?.id;
        if (currentProductId) {
            setReviewsData({ results: [], count: 0, next: null, previous: null });
            setReviewsError(null); setShowReviewForm(false); loadReviews(currentProductId);
        } else { setReviewsData({ results: [], count: 0, next: null, previous: null }); setReviewsError(null); setShowReviewForm(false); setReviewsLoading(false); }
    }, [product?.id, loadReviews]);

    const handleReviewAddedOrUpdated = useCallback(() => {
        if (product?.id) {
            setReviewsData({ results: [], count: 0, next: null, previous: null });
            loadReviews(product.id);
        }
        setShowReviewForm(false); setReviewToEdit(null);
        alert("Ваш отзыв успешно обработан.");
    }, [product?.id, loadReviews]);

    const handleEditReview = (review) => {
        setReviewToEdit(review); setShowReviewForm(true);
        document.getElementById('reviews-section')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    const handleDeleteReview = async (reviewId) => {
        if (!token) { alert("Ошибка: Необходима авторизация."); return; }
        if (window.confirm("Вы уверены, что хотите удалить этот отзыв?")) {
            try {
                await deleteReview(reviewId, token); alert("Отзыв успешно удален.");
                if (product?.id) { setReviewsData({ results: [], count: 0, next: null, previous: null }); loadReviews(product.id); }
            } catch (error) { console.error("Error deleting review:", error); alert(`Не удалось удалить отзыв: ${error.message}`); }
        }
    };

    const handleLoadMoreReviews = useCallback(() => {
        if (reviewsData.next && !reviewsLoading && product?.id) { loadReviews(product.id, reviewsData.next); }
    }, [reviewsData.next, reviewsLoading, product?.id, loadReviews]);

    if (!product) return <div className="container mx-auto p-10 text-center"><ErrorMessage message="Ошибка: Данные о товаре не были переданы." /></div>;
    const { id, name, images, features, category, brand, average_rating = 0, review_count = 0 } = product;
    let mainImageUrl = '/placeholder-image.png';
    if (Array.isArray(images) && images.length > 0) { const mainImage = images.find(img => img.main_image); mainImageUrl = mainImage?.image || images[0]?.image || '/placeholder-image.png'; }
    const safeFeatures = Array.isArray(features) ? features : [];
    const shortFeatures = safeFeatures.slice(0, 6);
    const hasMoreFeatures = safeFeatures.length > 6;

    return (
        <>
            <div className="max-w-4xl lg:max-w-6xl mx-auto p-4 sm:p-6 md:p-8 bg-white rounded-lg shadow-sm my-8">
                <div className="text-sm text-gray-500 mb-2"> {category?.name && <span>Категория: {category.name}</span>} {brand?.name && <span className="ml-4">Бренд: {brand.name}</span>} </div>
                <h1 className="text-2xl md:text-3xl font-bold mb-2">{name || 'Название товара'}</h1>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mb-4 text-sm">
                    {average_rating > 0 ? (<div className="flex items-center gap-1" title={`Рейтинг: ${average_rating.toFixed(1)} из 5`}> <Star className="h-4 w-4 fill-yellow-400 text-yellow-400"/> <span className="font-medium">{average_rating.toFixed(1)}</span> </div>) : (<span className="text-gray-500">Нет оценок</span>)}
                    <a href="#reviews-section" className="text-blue-600 hover:underline">{review_count > 0 ? `${review_count} ${review_count === 1 ? 'отзыв' : review_count < 5 ? 'отзыва' : 'отзывов'}` : 'Оставить первый отзыв'}</a>
                </div>
                <div className="flex flex-col md:flex-row gap-6 md:gap-8 mt-6">
                    <div className="md:w-1/2 lg:w-5/12"><ProductImage image={mainImageUrl} name={name}/></div>
                    <div className="md:w-1/2 lg:w-7/12 flex flex-col">
                        <ProductCharacteristics features={shortFeatures}/>
                        {hasMoreFeatures && (<Button variant="outline" className="mt-2 mb-6 text-sm self-start" onClick={() => setShowAllFeaturesModal(true)}>Все характеристики ({safeFeatures.length})</Button>)}
                        <div className="border-t pt-4 mt-4"><p className="text-gray-600 text-sm mb-1">Есть вопросы?</p><p className="text-gray-800 font-medium">+7 (000) 000-00-00</p></div>
                        <div className="mt-auto"><ProductPrice product={product}/></div>
                    </div>
                </div>
                <div id="reviews-section" className="mt-12 border-t pt-8">
                    <div className="flex flex-wrap justify-between items-center gap-4 mb-4">
                        <h2 className="text-xl font-semibold">Отзывы ({reviewsData.count || 0})</h2>
                        {isAuthenticated && !showReviewForm && !reviewToEdit && (<Button variant="outline" size="sm" onClick={() => { setReviewToEdit(null); setShowReviewForm(true); }}>Написать отзыв</Button>)}
                        {!isAuthenticated && <p className="text-sm text-gray-600">Чтобы оставить отзыв, <a href="/auth" className="text-blue-600 hover:underline">войдите</a>.</p>}
                    </div>
                    {showReviewForm && isAuthenticated && (<AddReviewForm key={reviewToEdit ? reviewToEdit.id : 'new'} productId={id} reviewToEdit={reviewToEdit} onReviewAdded={handleReviewAddedOrUpdated} onCancel={() => { setShowReviewForm(false); setReviewToEdit(null); }} />)}
                    <ProductReviews reviews={reviewsData.results} loading={reviewsLoading && reviewsData.results.length === 0} error={reviewsError} totalReviewCount={reviewsData.count} onRetry={product?.id ? () => loadReviews(product.id) : undefined} onEditReview={handleEditReview} onDeleteReview={handleDeleteReview} />
                    {reviewsData.next && !reviewsLoading && (<div className="text-center mt-6"><Button onClick={handleLoadMoreReviews} variant="outline">Загрузить еще отзывы</Button></div>)}
                    {reviewsLoading && reviewsData.results.length > 0 && (<div className="text-center mt-6"><Button variant="outline" disabled className="inline-flex items-center"><RefreshCw className="h-4 w-4 mr-2 animate-spin"/> Загрузка...</Button></div>)}
                </div>
            </div>
            <Modal isOpen={showAllFeaturesModal} onClose={() => setShowAllFeaturesModal(false)} title={`Характеристики: ${name || ''}`} size="lg">
                {safeFeatures.length > 0 ? (<ul className="space-y-2 max-h-[60vh] overflow-y-auto pr-2 -mr-2">{safeFeatures.map((feature, index) => (<li key={feature.id || feature.feature_id || `feature-${index}`} className="flex flex-col sm:flex-row text-sm border-b pb-1.5 last:border-b-0"><span className="text-gray-600 w-full sm:w-1/3 md:w-2/5 flex-shrink-0 font-medium pr-2 mb-0.5 sm:mb-0">{feature.feature_name}:</span><span className="text-gray-800 break-words w-full sm:w-2/3 md:w-3/5">{feature.value}</span></li>))}</ul>) : ( <p className="text-gray-500">Характеристики не указаны.</p> )}
                <div className="mt-6 text-right border-t pt-4 -mx-4 sm:-mx-6 px-4 sm:px-6 bg-gray-50 rounded-b-lg"><Button variant="primary" onClick={() => setShowAllFeaturesModal(false)}>Закрыть</Button></div>
            </Modal>
        </>
    );
};

export default ProductDetail;
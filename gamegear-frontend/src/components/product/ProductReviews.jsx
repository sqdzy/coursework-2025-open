import React, {useState} from 'react';
import {Star, Edit3, Trash2, Maximize2} from 'lucide-react';
import {useAuth} from '../context/AuthContext';
import Modal from '../ui/Modal';
import Button from '../ui/Button';
import LoadingSpinner from '../ui/LoadingSpinner';
import ErrorMessage from '../ui/ErrorMessage';

const formatDate = (dateString) => {
    if (!dateString) return '';
    try {
        return new Intl.DateTimeFormat('ru-RU', {
            year: 'numeric', month: 'short', day: 'numeric',
            hour: '2-digit', minute: '2-digit'
        }).format(new Date(dateString));
    } catch (e) {
        console.warn("Date formatting failed in ProductReviews:", e);
        return dateString;
    }
};

const ProductReviews = ({reviews, loading, error, onRetry, totalReviewCount, onEditReview, onDeleteReview}) => {
    const {user: currentUser, isAuthenticated} = useAuth();
    const [zoomedImage, setZoomedImage] = useState(null);

    if (loading) {
        return <div className="py-4 text-center"><LoadingSpinner text="Загрузка отзывов..."/></div>;
    }

    if (error) {
        return <div className="py-4"><ErrorMessage message={error} onRetry={onRetry}/></div>;
    }

    if (!reviews || reviews.length === 0) {
        return (
            <div className="text-center py-6 text-gray-500">
                {totalReviewCount > 0 ? "Одобренных отзывов пока нет." : "Отзывов пока нет. Будьте первым!"}
            </div>
        );
    }

    return (
        <div className="space-y-6 mt-6">
            {reviews.map((review) => (
                <div key={review.id} className="border-b border-gray-200 pb-5 last:border-b-0">
                    <div className="flex items-start justify-between mb-2 gap-x-4 gap-y-1 flex-wrap">
                        <span className="font-semibold text-gray-800 break-words">
                            {review.user?.first_name && review.user?.last_name
                                ? `${review.user.first_name} ${review.user.last_name}`
                                : review.user?.username || 'Анонимный пользователь'}
                        </span>
                        <span className="text-xs text-gray-500 flex-shrink-0 whitespace-nowrap">
                            {formatDate(review.created_at)}
                        </span>
                    </div>
                    <div className="flex items-center mb-3">
                        {[...Array(5)].map((_, i) => (
                            <Star
                                key={i}
                                className={`h-4 w-4 ${i < review.rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300'}`}
                                aria-hidden="true"
                            />
                        ))}
                    </div>
                    <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap mb-3">
                        {review.text}
                    </p>

                    {review.images && review.images.length > 0 && (
                        <div className="flex flex-wrap gap-2 mb-3">
                            {review.images.map(img => (
                                <button
                                    key={img.id}
                                    onClick={() => setZoomedImage(img.image)}
                                    className="w-16 h-16 sm:w-20 sm:h-20 border rounded-md overflow-hidden group relative focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-1"
                                    aria-label="Увеличить изображение"
                                >
                                    <img
                                        src={img.image}
                                        alt={`Изображение к отзыву ${review.id}`}
                                        className="w-full h-full object-cover"
                                        loading="lazy"
                                    />
                                    <div
                                        className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 flex items-center justify-center transition-all duration-200 opacity-0 group-hover:opacity-100">
                                        <Maximize2 size={20} smSize={24} className="text-white"/>
                                    </div>
                                </button>
                            ))}
                        </div>
                    )}

                    {isAuthenticated && currentUser?.id === review.user?.id && (
                        <div className="mt-2 text-xs space-x-3">
                            <button
                                onClick={() => onEditReview(review)}
                                className="text-blue-600 hover:text-blue-700 hover:underline inline-flex items-center gap-1 transition-colors"
                            >
                                <Edit3 size={14}/> Редактировать
                            </button>
                            <button
                                onClick={() => onDeleteReview(review.id)}
                                className="text-red-600 hover:text-red-700 hover:underline inline-flex items-center gap-1 transition-colors"
                            >
                                <Trash2 size={14}/> Удалить
                            </button>
                        </div>
                    )}
                </div>
            ))}

            {zoomedImage && (
                <Modal
                    isOpen={!!zoomedImage}
                    onClose={() => setZoomedImage(null)}
                    title="Просмотр изображения"
                    size="2xl"
                    footerContent={
                        <Button variant="primary" onClick={() => setZoomedImage(null)}>Закрыть</Button>
                    }
                >
                    <div className="flex justify-center items-center w-full h-full p-1">
                        <img
                            src={zoomedImage}
                            alt="Увеличенное изображение отзыва"
                            className="max-w-full max-h-[calc(90vh-160px)] object-contain rounded"
                        />
                    </div>
                </Modal>
            )}
        </div>
    );
};

export default ProductReviews;

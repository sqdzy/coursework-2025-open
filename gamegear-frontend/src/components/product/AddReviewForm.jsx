import React, { useState, useEffect, useRef } from 'react';
import { Star, UploadCloud, X as CloseIcon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Button from '../ui/Button';
import ErrorMessage from '../ui/ErrorMessage';

const MAX_IMAGES = 2;
const MAX_IMAGE_SIZE_MB = 5;

const AddReviewForm = ({ productId, onReviewAdded, onCancel, reviewToEdit = null }) => {
    const { token } = useAuth();
    const isEditing = !!reviewToEdit;

    const [rating, setRating] = useState(0);
    const [hoverRating, setHoverRating] = useState(0);
    const [text, setText] = useState('');
    const [images, setImages] = useState([]);
    const [existingImages, setExistingImages] = useState([]);
    const [imagesToDeleteIds, setImagesToDeleteIds] = useState([]);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const fileInputRef = useRef(null);

    useEffect(() => {
        if (reviewToEdit) {
            setRating(reviewToEdit.rating || 0);
            setText(reviewToEdit.text || '');
            setExistingImages(reviewToEdit.images || []);
            setImages([]);
            setImagesToDeleteIds([]);
            setError(null);
        } else {
            setRating(0);
            setText('');
            setExistingImages([]);
            setImages([]);
            setImagesToDeleteIds([]);
            setError(null);
        }
    }, [reviewToEdit]);

    const handleImageChange = (e) => {
        setError(null);
        const files = Array.from(e.target.files);
        const newImages = [];
        let currentTotalImages = images.length + existingImages.filter(img => !imagesToDeleteIds.includes(img.id)).length;

        for (const file of files) {
            if (currentTotalImages >= MAX_IMAGES) {
                setError(`Можно загрузить не более ${MAX_IMAGES} изображений.`); break;
            }
            if (file.size > MAX_IMAGE_SIZE_MB * 1024 * 1024) {
                setError(`Файл "${file.name}" слишком большой (макс. ${MAX_IMAGE_SIZE_MB} МБ).`); continue;
            }
            if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
                 setError(`Файл "${file.name}" имеет недопустимый тип.`); continue;
            }
            newImages.push(file);
            currentTotalImages++;
        }
        setImages(prev => [...prev, ...newImages]);
        if (fileInputRef.current) fileInputRef.current.value = "";
    };

    const removeNewImage = (index) => {
        setImages(prev => prev.filter((_, i) => i !== index));
    };

    const toggleDeleteExistingImage = (imageId) => {
        setImagesToDeleteIds(prev =>
            prev.includes(imageId) ? prev.filter(id => id !== imageId) : [...prev, imageId]
        );
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        if (!token) { setError('Необходимо авторизоваться.'); return; }
        if (rating === 0) { setError('Выберите оценку.'); return; }
        if (!text.trim() || text.trim().length < 10) { setError('Текст отзыва слишком короткий (минимум 10 символов).'); return; }
        setSubmitting(true);
        try {
            const { createReview, updateReview } = await import('../../services/api');
            if (isEditing && reviewToEdit) {
                const dataToUpdate = { rating, text };
                if (images.length > 0) dataToUpdate.imagesToAdd = images;
                if (imagesToDeleteIds.length > 0) dataToUpdate.imagesToDeleteIds = imagesToDeleteIds;
                await updateReview(reviewToEdit.id, dataToUpdate, token);
            } else {
                await createReview(productId, rating, text, images, token);
            }
            onReviewAdded();
        } catch (err) {
             if (err.validationErrors) {
                 let errorMessages = [];
                 for (const field in err.validationErrors) {
                     errorMessages.push(`${field === 'non_field_errors' ? '' : field + ': '}${err.validationErrors[field].join ? err.validationErrors[field].join(', ') : err.validationErrors[field]}`);
                 }
                 setError(errorMessages.join(' '));
             } else {
                setError(err.message || 'Не удалось отправить отзыв.');
             }
            console.error('Review submission error:', err);
        } finally {
            setSubmitting(false);
        }
    };

    const totalVisibleImages = (existingImages || []).filter(img => !imagesToDeleteIds.includes(img.id)).length + images.length;

    return (
        <form onSubmit={handleSubmit} className="border rounded-md p-4 my-6 bg-gray-50 shadow-sm">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">{isEditing ? 'Редактировать отзыв' : 'Оставить отзыв'}</h3>
            {error && <ErrorMessage message={error} className="mb-3" />}
            <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Ваша оценка:</label>
                <div className="flex items-center space-x-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                        <button type="button" key={star} className="focus:outline-none" title={`${star} из 5`} onMouseEnter={() => setHoverRating(star)} onMouseLeave={() => setHoverRating(0)} onClick={() => setRating(star)} aria-label={`Оценка ${star}`}>
                            <Star className={`h-6 w-6 cursor-pointer transition-colors duration-150 ${(hoverRating || rating) >= star ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300 hover:text-yellow-300'}`} />
                        </button>
                    ))}
                    {(hoverRating || rating) > 0 && (<span className="ml-3 text-sm text-gray-600 font-medium">({hoverRating || rating}/5)</span>)}
                </div>
            </div>
            <div className="mb-4">
                <label htmlFor="reviewText" className="block text-sm font-medium text-gray-700 mb-1">Ваш комментарий:</label>
                <textarea id="reviewText" rows="4" className="w-full p-2 border border-gray-300 rounded-md focus:ring-orange-500 focus:border-orange-500 shadow-sm text-sm disabled:bg-gray-100" value={text} onChange={(e) => setText(e.target.value)} placeholder="Поделитесь впечатлениями..." required disabled={submitting} aria-label="Текст отзыва" />
            </div>
            <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Фотографии (до {MAX_IMAGES} шт., до {MAX_IMAGE_SIZE_MB}МБ каждая, JPG/PNG/WebP)</label>
                {isEditing && existingImages.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-2">
                        {existingImages.map(img => (
                            <div key={img.id} className="relative w-20 h-20 border rounded">
                                <img src={img.image} alt="Фото отзыва" className="w-full h-full object-cover rounded" />
                                <button type="button" onClick={() => toggleDeleteExistingImage(img.id)} className={`absolute -top-1 -right-1 p-0.5 rounded-full text-white ${imagesToDeleteIds.includes(img.id) ? 'bg-red-500 hover:bg-red-600' : 'bg-gray-400 hover:bg-gray-500'}`} title={imagesToDeleteIds.includes(img.id) ? "Отменить удаление" : "Удалить это фото"}> <CloseIcon size={14} /> </button>
                                {imagesToDeleteIds.includes(img.id) && (<div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center text-white text-xs font-bold">УДАЛЕНО</div>)}
                            </div>
                        ))}
                    </div>
                )}
                {images.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-2">
                        {images.map((file, index) => (
                            <div key={index} className="relative w-20 h-20 border rounded">
                                <img src={URL.createObjectURL(file)} alt={file.name} className="w-full h-full object-cover rounded" />
                                <button type="button" onClick={() => removeNewImage(index)} className="absolute -top-1 -right-1 bg-red-500 text-white p-0.5 rounded-full hover:bg-red-600" title="Убрать фото"> <CloseIcon size={14} /> </button>
                            </div>
                        ))}
                    </div>
                )}
                 {totalVisibleImages < MAX_IMAGES && (
                    <label className="mt-1 flex justify-center items-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md cursor-pointer hover:border-orange-400 bg-white">
                        <div className="space-y-1 text-center">
                            <UploadCloud className="mx-auto h-10 w-10 text-gray-400" />
                            <div className="flex text-sm text-gray-600">
                                <span className="relative rounded-md font-medium text-orange-600 hover:text-orange-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-orange-500">Загрузить файлы</span>
                                <input ref={fileInputRef} id="review-images-upload" name="uploaded_images" type="file" className="sr-only" multiple accept="image/jpeg,image/png,image/webp" onChange={handleImageChange} disabled={submitting || totalVisibleImages >= MAX_IMAGES} />
                            </div>
                            <p className="text-xs text-gray-500">или перетащите сюда</p>
                        </div>
                    </label>
                 )}
            </div>
            <div className="flex justify-end gap-3 pt-2">
                <Button type="button" onClick={onCancel} variant="outline" disabled={submitting}>Отмена</Button>
                <Button type="submit" variant="primary" disabled={submitting || rating === 0 || !text.trim()}>{submitting ? 'Отправка...' : (isEditing ? 'Сохранить' : 'Отправить отзыв')}</Button>
            </div>
        </form>
    );
};

export default AddReviewForm;
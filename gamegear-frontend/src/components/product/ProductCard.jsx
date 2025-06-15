import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Star, ShoppingCart, Check } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Button from '../ui/Button';

const formatPrice = (price) => {
    if (price === null || price === undefined) return '';
    return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(price);
};

const PLACEHOLDER_IMAGE = '/placeholder-image.png';

const ProductCard = ({ product }) => {
    const initialImageSrc = product?.main_image || PLACEHOLDER_IMAGE;
    const [imageSrc, setImageSrc] = useState(initialImageSrc);
    const [hasImageError, setHasImageError] = useState(!product?.main_image);

    const { isAuthenticated, addToCart, cart } = useAuth();
    const navigate = useNavigate();
    const [isAdding, setIsAdding] = useState(false);
    const [justAdded, setJustAdded] = useState(false);

    useEffect(() => {
        const newSrc = product?.main_image || PLACEHOLDER_IMAGE;
        if (newSrc !== imageSrc) {
            setImageSrc(newSrc);
            setHasImageError(!product?.main_image);
        }
    }, [product?.main_image, imageSrc]);

    const handleImageError = useCallback(() => {
        if (!hasImageError && imageSrc !== PLACEHOLDER_IMAGE) {
            setImageSrc(PLACEHOLDER_IMAGE);
            setHasImageError(true);
        }
    }, [hasImageError, imageSrc]);

    if (!product) return null;

    const { id, name, price, base_price, promotional_price, stock, average_rating, review_count, promotion_name } = product;

    const displayPrice = price;
    const oldPrice = (base_price && price < base_price) ? base_price : null;
    const isOutOfStock = stock === 0;

    const handleAddToCartClick = async (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!isAuthenticated) {
            if (window.confirm("Для добавления в корзину необходимо войти. Перейти на страницу входа?")) {
                navigate('/auth', { state: { from: window.location } });
            } return;
        }
        if (justAdded || isAdding || isOutOfStock) return;
        setIsAdding(true); setJustAdded(false);
        const result = await addToCart(product.id, 1);
        setIsAdding(false);
        if (result.success) {
            setJustAdded(true);
            setTimeout(() => setJustAdded(false), 2000);
        } else {
            alert(`Ошибка добавления в корзину: ${result.error || 'Неизвестная ошибка'}`);
        }
    };

    const isInCart = isAuthenticated && cart.items.some(item => item.product?.id === product.id);

    return (
        <div className="group block border rounded-lg overflow-hidden shadow hover:shadow-md transition-shadow duration-200 bg-white flex flex-col h-full">
            <Link to={`/products/${id}`} className="contents">
                <div className="aspect-square bg-gray-50 flex items-center justify-center p-2 overflow-hidden relative">
                    <img src={imageSrc} alt={name || 'Товар'} className="max-w-full max-h-full object-contain group-hover:scale-105 transition-transform duration-300 mix-blend-multiply" loading="lazy" onError={handleImageError} />
                    {(promotional_price !== null || promotion_name) && (<span className="absolute top-2 left-2 bg-red-500 text-white text-xs font-semibold px-2 py-0.5 rounded">Акция!</span>)}
                    {isOutOfStock && (<div className="absolute inset-0 bg-white bg-opacity-60 flex items-center justify-center"><span className="text-sm font-semibold text-gray-500 border-2 border-gray-400 rounded px-2 py-1 rotate-[-10deg]">Нет в наличии</span></div>)}
                </div>
                <div className="p-3 sm:p-4 flex-grow">
                    {review_count > 0 && (<div className="flex items-center gap-1 mb-1 text-xs"><Star className="h-3.5 w-3.5 fill-yellow-400 text-yellow-400" /><span className="font-medium text-gray-700">{average_rating?.toFixed(1)}</span><span className="text-gray-400">({review_count})</span></div>)}
                    <h3 className="text-sm font-semibold text-gray-800 mb-2 h-10 leading-5 overflow-hidden group-hover:text-orange-600">{name}</h3>
                </div>
            </Link>
            <div className="p-3 sm:p-4 border-t mt-auto flex items-center justify-between gap-2">
                 <div className='flex-shrink min-w-0'>
                     <span className={`block text-base md:text-lg font-bold truncate ${oldPrice ? 'text-red-600' : 'text-gray-900'}`}>{formatPrice(displayPrice)}</span>
                     {oldPrice && (<span className="block text-xs md:text-sm text-gray-400 line-through truncate">{formatPrice(oldPrice)}</span>)}
                </div>
                 <Button onClick={handleAddToCartClick} disabled={isAdding || (isInCart && !justAdded) || isOutOfStock} size="sm" variant={(isInCart || justAdded) ? "secondary" : "primary"} className={`flex-shrink-0 transition-all ${justAdded ? 'bg-green-500 hover:bg-green-600 text-white' : ''} ${isOutOfStock ? 'bg-gray-300 hover:bg-gray-300 cursor-not-allowed' : ''}`} title={isOutOfStock ? "Нет в наличии" : !isAuthenticated ? "Войдите, чтобы добавить" : isInCart ? "В корзине" : "Добавить в корзину"}>
                    {isAdding ? <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div> : justAdded ? <Check size={16} /> : <ShoppingCart size={16} />}
                 </Button>
            </div>
        </div>
    );
};

export default ProductCard;
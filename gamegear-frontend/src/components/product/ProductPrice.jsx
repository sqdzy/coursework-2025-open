import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShoppingCart, Check, Tag } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Button from '../ui/Button';

const formatPrice = (price) => {
    if (price === null || price === undefined) return '';
    const numPrice = parseFloat(price);
    if (isNaN(numPrice)) return ' - ';
    return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(numPrice);
};

const ProductPrice = ({ product }) => {
    const { isAuthenticated, addToCart, cart } = useAuth();
    const navigate = useNavigate();
    const [isAdding, setIsAdding] = useState(false);
    const [justAdded, setJustAdded] = useState(false);

    if (!product) { return <div className="mt-6 pt-6 border-t text-red-500">Ошибка: Данные о товаре не переданы.</div>; }

    const productId = product?.id;
    const actual_price = product?.price;
    const base_price = product?.base_price;
    const promotional_price = product?.promotional_price;
    const stock = product?.stock;

    const hasDiscount = promotional_price !== null && actual_price < base_price;
    const oldPrice = hasDiscount ? base_price : null;
    const isOutOfStock = stock === 0;

    if (!productId) { return <div className="mt-6 pt-6 border-t text-red-500">Ошибка: Не найден ID товара.</div>; }

    const handleAddToCartClick = async () => {
        if (!isAuthenticated) { if (window.confirm("Для добавления в корзину необходимо войти. Перейти на страницу входа?")) { navigate('/auth', { state: { from: window.location } }); } return; }
        if (justAdded || isAdding || isOutOfStock) return;
        setIsAdding(true); setJustAdded(false);
        const result = await addToCart(productId, 1);
        setIsAdding(false);
        if (result.success) { setJustAdded(true); setTimeout(() => setJustAdded(false), 2000);
        } else { alert(`Ошибка добавления в корзину: ${result.error || 'Неизвестная ошибка'}`); }
    };

    const isInCart = isAuthenticated && cart.items.some(item => item.product?.id === productId);
    const formattedDisplayPrice = formatPrice(actual_price);

    return (
        <div className="mt-6 pt-6 border-t">
            <div className="mb-4 flex flex-wrap items-baseline gap-x-3 gap-y-1">
                <span className={`text-3xl font-bold ${hasDiscount ? 'text-red-600' : 'text-gray-900'}`}>{formattedDisplayPrice || 'Цена не указана'}</span>
                {oldPrice && (<span className="text-xl text-gray-400 line-through">{formatPrice(oldPrice)}</span>)}
                {hasDiscount && (<span className="inline-flex items-center bg-red-100 text-red-700 text-xs font-semibold px-2 py-0.5 rounded"><Tag size={14} className='mr-1'/> Скидка!</span>)}
            </div>

            <div className='mb-4'>
                {isOutOfStock ? (
                    <p className="text-sm font-semibold text-red-600">Нет в наличии</p>
                ) : (
                    <p className="text-sm font-semibold text-green-600">В наличии: {stock} шт.</p>
                )}
            </div>

            <Button
                onClick={handleAddToCartClick}
                disabled={isAdding || (isInCart && !justAdded) || isOutOfStock}
                size="lg"
                variant={(isInCart || justAdded) ? "secondary" : "primary"}
                className={`w-full sm:w-auto transition-all ${justAdded ? 'bg-green-500 hover:bg-green-600 text-white' : ''} ${isOutOfStock ? 'bg-gray-300 hover:bg-gray-300 cursor-not-allowed' : ''}`}
                title={isOutOfStock ? "Нет в наличии" : !isAuthenticated ? "Войдите, чтобы добавить" : isInCart ? "В корзине" : "Добавить в корзину"}
            >
                 {isAdding ? <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin mx-auto"></div> : justAdded ? <Check size={20} /> : isOutOfStock ? 'Нет в наличии' : <span className='flex items-center justify-center'><ShoppingCart size={20} className="mr-2"/> В корзину</span>}
            </Button>

            {!isAuthenticated && (<p className="text-xs text-gray-500 mt-2"> <button onClick={() => navigate('/auth', { state: { from: window.location } })} className="text-orange-600 hover:underline">Войдите</button>, чтобы добавить товар в корзину. </p> )}
        </div>
    );
};

export default ProductPrice;
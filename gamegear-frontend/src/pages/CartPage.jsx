import React, {useEffect} from 'react';
import {Link, useNavigate} from 'react-router-dom';
import {useAuth} from '../components/context/AuthContext';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorMessage from '../components/ui/ErrorMessage';
import Button from '../components/ui/Button';
import {Trash2, Plus, Minus} from 'lucide-react';


const formatPrice = (price) => {
    const numPrice = parseFloat(price);
    if (isNaN(numPrice)) return ' - ';
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    }).format(numPrice);
};

const CartPage = () => {

    const {cart, isAuthenticated, isLoading: authLoading, fetchCart, updateCartQuantity, removeFromCart} = useAuth();
    const navigate = useNavigate();


    useEffect(() => {
        if (!authLoading && !isAuthenticated) {
            console.log("Not authenticated, redirecting from CartPage to /auth");
            navigate('/auth', {state: {from: {pathname: '/cart'}}});
        }


    }, [isAuthenticated, authLoading, navigate]);


    const handleQuantityChange = async (itemId, newQuantity) => {

        await updateCartQuantity(itemId, newQuantity);
    };


    const handleRemoveItem = async (itemId) => {
        await removeFromCart(itemId);
    };


    const cartItems = cart?.items || [];
    const cartSubtotal = cartItems.reduce((sum, item) => {
        const itemTotalPrice = parseFloat(item?.total_price ?? 0);
        return sum + (isNaN(itemTotalPrice) ? 0 : itemTotalPrice);
    }, 0);
    const totalCartQuantity = cartItems.reduce((sum, item) => sum + (item?.quantity ?? 0), 0);


    if (authLoading || (isAuthenticated && cart.loading && cartItems.length === 0)) {
        return <div className="container mx-auto px-4 py-10 text-center"><LoadingSpinner text="Загрузка корзины..."/>
        </div>;
    }


    if (!isAuthenticated && !authLoading) {

        return <div className="container mx-auto px-4 py-10 text-center"><ErrorMessage
            message="Для доступа к корзине необходимо войти."/></div>;
    }


    if (cart.error) {
        return <div className="container mx-auto px-4 py-10"><ErrorMessage message={cart.error} onRetry={fetchCart}/>
        </div>;
    }


    if (!cart.loading && cartItems.length === 0) {
        return (
            <div className="container mx-auto px-4 py-10 text-center">
                <h1 className="text-2xl font-semibold mb-4">Ваша корзина пуста</h1>
                <p className="text-gray-600 mb-6">Самое время добавить что-нибудь!</p>
                <Link to="/">
                    <Button variant="primary">Перейти к товарам</Button>
                </Link>
            </div>
        );
    }


    return (
        <div className="container mx-auto px-4 py-6 md:py-8">
            <h1 className="text-2xl md:text-3xl font-bold mb-6">Корзина</h1>
            <div className="flex flex-col lg:flex-row gap-8 lg:gap-12">


                <div className="flex-grow lg:w-2/3">
                    <ul className="space-y-4">
                        {cartItems.map((item) => {

                            const currentItemPrice = item?.current_price_per_item;
                            const baseItemPrice = item?.product?.base_price;
                            const oldItemPrice = (baseItemPrice && currentItemPrice < baseItemPrice) ? baseItemPrice : null;
                            const productLink = item?.product?.id ? `/products/${item.product.id}` : '#';

                            return (
                                <li key={item.id}
                                    className="flex flex-col sm:flex-row items-start sm:items-center gap-4 border rounded-lg p-4 bg-white shadow-sm hover:shadow-md transition-shadow">

                                    <Link to={productLink}
                                          className="flex-shrink-0 w-20 h-20 sm:w-24 sm:h-24 bg-gray-50 rounded overflow-hidden flex items-center justify-center border">
                                        <img src={item.product?.main_image || '/placeholder-image.png'}
                                             alt={item.product?.name}
                                             className="max-w-full max-h-full object-contain mix-blend-multiply"
                                             onError={(e) => {
                                                 e.target.onerror = null;
                                                 e.target.src = '/placeholder-image.png';
                                             }}/>
                                    </Link>

                                    <div className="flex-grow text-center sm:text-left w-full sm:w-auto">
                                        <Link to={productLink}
                                              className="font-semibold text-gray-800 hover:text-orange-600 mb-1 block text-base leading-tight">{item.product?.name || 'Название не найдено'}</Link>
                                        <div className="text-sm text-gray-600 block mt-1">
                                            <span
                                                className={`font-medium ${oldItemPrice ? 'text-orange-600' : 'text-gray-800'}`}>{formatPrice(currentItemPrice)}</span>
                                            {oldItemPrice && (<span
                                                className="ml-2 line-through text-gray-400">{formatPrice(oldItemPrice)}</span>)}
                                            <span className='ml-1 text-gray-400'> / шт.</span>
                                        </div>
                                    </div>

                                    <div
                                        className="flex items-center gap-1 border rounded px-1 py-1 my-2 sm:my-0 flex-shrink-0 bg-gray-50">
                                        <Button
                                            onClick={() => handleQuantityChange(item.id, item.quantity - 1)}
                                            disabled={cart.loading || item.quantity <= 1}
                                            variant="ghost"
                                            size="sm"
                                            className="px-2 text-gray-500 hover:text-red-600 disabled:opacity-40 disabled:cursor-not-allowed"
                                            title="Уменьшить"
                                        >
                                            <Minus size={16}/>
                                        </Button>

                                        <input
                                            type="number"
                                            min="1"
                                            value={item.quantity}
                                            onChange={(e) => {
                                                const newQuantity = parseInt(e.target.value, 10);
                                                if (!isNaN(newQuantity) && newQuantity >= 1) {
                                                    handleQuantityChange(item.id, newQuantity);
                                                } else if (e.target.value === '') {


                                                }
                                            }}
                                            onBlur={(e) => {
                                                if (e.target.value === '') {
                                                    handleQuantityChange(item.id, 1);
                                                }
                                            }}
                                            disabled={cart.loading}
                                            className="font-medium w-10 text-center border-x bg-white text-sm focus:outline-none focus:ring-1 focus:ring-orange-500"
                                            aria-label={`Количество ${item.product?.name}`}
                                        />
                                        <Button
                                            onClick={() => handleQuantityChange(item.id, item.quantity + 1)}
                                            disabled={cart.loading}
                                            variant="ghost"
                                            size="sm"
                                            className="px-2 text-gray-500 hover:text-green-600 disabled:opacity-50"
                                            title="Увеличить"
                                        >
                                            <Plus size={16}/>
                                        </Button>
                                    </div>

                                    <div
                                        className="flex flex-col items-center sm:items-end gap-1 ml-0 sm:ml-auto flex-shrink-0 w-full sm:w-28 text-right mt-2 sm:mt-0">
                                        <span className="font-semibold text-md">{formatPrice(item.total_price)}</span>
                                        <Button
                                            onClick={() => handleRemoveItem(item.id)}
                                            disabled={cart.loading}
                                            variant="ghost"
                                            size="sm"
                                            className="text-xs text-gray-400 hover:text-red-500 disabled:opacity-50 flex items-center justify-end w-full p-0 h-auto"
                                            title="Удалить товар"
                                        >
                                            <Trash2 size={14} className="mr-1"/> Удалить
                                        </Button>
                                    </div>
                                </li>
                            );
                        })}
                    </ul>
                </div>


                <div className="lg:w-1/3">
                    <div className="sticky top-24 bg-white border rounded-lg p-6 shadow-lg">
                        <h2 className="text-xl font-semibold mb-4 border-b pb-3">Сумма заказа</h2>
                        <div className="space-y-2 mb-4">
                            <div className="flex justify-between text-gray-700">
                                <span>Товары ({totalCartQuantity} шт.)</span>
                                <span>{formatPrice(cartSubtotal)}</span>
                            </div>
                            <div className="flex justify-between text-gray-700">
                                <span>Доставка</span>
                                <span className='text-green-600 font-medium'>Бесплатно</span>
                            </div>
                        </div>
                        <div className="flex justify-between font-bold text-xl border-t pt-4 mt-4">
                            <span>Итого к оплате</span>
                            <span>{formatPrice(cartSubtotal)}</span>
                        </div>
                        <Link to="/checkout" className="block mt-6">
                            <Button variant="primary" className="w-full" size="lg">
                                Перейти к оформлению
                            </Button>
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CartPage;

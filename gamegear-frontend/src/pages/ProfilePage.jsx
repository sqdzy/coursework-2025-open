import React, {useState, useEffect, useCallback} from 'react';
import {useNavigate, Link} from 'react-router-dom';
import {useAuth} from '../components/context/AuthContext';
import {fetchUserDetails, fetchUserOrders} from '../services/api';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorMessage from '../components/ui/ErrorMessage';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import EditProfileForm from '../components/profile/EditProfileForm';
import {CheckCircle, AlertCircle} from 'lucide-react';


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


const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
        return new Intl.DateTimeFormat('ru-RU', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(dateString));
    } catch (e) {
        console.warn("Date formatting failed:", e);
        return dateString;
    }
};

const ProfilePage = () => {
    const {isAuthenticated, isLoading: authLoading, token, logout, user: contextUser} = useAuth();
    const navigate = useNavigate();

    const [userData, setUserData] = useState(null);
    const [ordersData, setOrdersData] = useState({count: 0, next: null, previous: null, results: []});
    const [loadingUser, setLoadingUser] = useState(true);
    const [loadingOrders, setLoadingOrders] = useState(true);
    const [error, setError] = useState(null);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [updateSuccessMessage, setUpdateSuccessMessage] = useState('');


    const loadUserData = useCallback(async () => {
        if (!token) return;
        setLoadingUser(true);

        try {
            console.log("ProfilePage: Fetching user details...");
            const data = await fetchUserDetails(token);
            setUserData(data);
            setError(null);
        } catch (err) {
            console.error("Error fetching user data:", err);
            setError(err.message || 'Не удалось загрузить данные профиля.');
            if (err.message && (err.message.includes('401') || err.message.includes('credentials'))) {
                logout();
                navigate('/auth', {state: {from: {pathname: '/profile'}}});
            }
        } finally {
            setLoadingUser(false);
        }
    }, [token, logout, navigate]);


    const loadOrders = useCallback(async (url = null) => {
        if (!token) return;
        setLoadingOrders(true);
        try {
            console.log(`ProfilePage: Fetching orders from ${url || 'first page'}...`);
            const data = await fetchUserOrders(token, url);
            setOrdersData(data);

            if (error && error.includes('заказ')) setError(null);
        } catch (err) {
            console.error("Error fetching orders:", err);
            setError(err.message || 'Не удалось загрузить историю заказов.');
            if (err.message && (err.message.includes('401') || err.message.includes('credentials'))) {
                logout();
                navigate('/auth', {state: {from: {pathname: '/profile'}}});
            }
        } finally {
            setLoadingOrders(false);
        }
    }, [token, logout, navigate, error]);


    useEffect(() => {
        if (!authLoading) {
            if (!isAuthenticated) {
                navigate('/auth', {state: {from: {pathname: '/profile'}}});
            } else if (token) {
                console.log("ProfilePage: Auth loaded, loading user data and orders...");
                if (!userData) loadUserData();
                loadOrders();
            }
        }

    }, [isAuthenticated, authLoading, token, navigate]);


    const handleNextOrders = () => {
        if (ordersData.next) loadOrders(ordersData.next);
    };
    const handlePreviousOrders = () => {
        if (ordersData.previous) loadOrders(ordersData.previous);
    };


    const handleProfileUpdateSuccess = (updatedApiData) => {

        setUserData(prev => ({...prev, ...updatedApiData}));


        const updatedLocalStorageUser = {...contextUser, ...updatedApiData};
        localStorage.setItem('authUser', JSON.stringify(updatedLocalStorageUser));


        setIsEditModalOpen(false);
        setUpdateSuccessMessage("Профиль успешно обновлен!");

        setTimeout(() => setUpdateSuccessMessage(''), 3000);
    };


    const isLoading = authLoading || loadingUser;

    if (isLoading) {
        return <div className="container mx-auto px-4 py-10 text-center"><LoadingSpinner text="Загрузка профиля..."/>
        </div>;
    }
    if (!isAuthenticated) {
        return <div className="container mx-auto px-4 py-10 text-center"><ErrorMessage
            message="Для доступа к профилю необходимо войти."/></div>;
    }
    if (error && !userData && !loadingUser) {
        return <div className="container mx-auto px-4 py-10"><ErrorMessage message={error} onRetry={loadUserData}/>
        </div>;
    }
    if (!userData) {
        return <div className="container mx-auto px-4 py-10"><ErrorMessage
            message="Не удалось загрузить данные пользователя." onRetry={loadUserData}/></div>;
    }

    return (
        <div className="container mx-auto px-4 py-6 md:py-8">
            <h1 className="text-2xl md:text-3xl font-bold mb-6">Личный кабинет</h1>

            {updateSuccessMessage && (
                <div
                    className="mb-6 p-3 flex items-center gap-2 bg-green-50 border border-green-200 text-green-700 text-sm rounded-md">
                    <CheckCircle size={18}/> {updateSuccessMessage}
                </div>
            )}

            {error && <ErrorMessage message={error} className="mb-6"
                                    onRetry={error.includes('заказ') ? loadOrders : loadUserData}/>}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 lg:gap-12">
                <div className="lg:col-span-1">
                    <div className="bg-white p-6 rounded-lg shadow-sm border">
                        <h2 className="text-xl font-semibold mb-4">Профиль</h2>
                        <div className="space-y-2 text-sm">
                            <p><span className="font-medium text-gray-600">Имя пользователя:</span> {userData?.username}
                            </p>
                            <p><span className="font-medium text-gray-600">Email:</span> {userData?.email || '-'}</p>
                            <p><span className="font-medium text-gray-600">Имя:</span> {userData?.first_name || '-'}</p>
                            <p><span className="font-medium text-gray-600">Фамилия:</span> {userData?.last_name || '-'}
                            </p>
                            <p><span
                                className="font-medium text-gray-600">Дата регистрации:</span> {formatDate(userData?.created_at)}
                            </p>
                            {/* <p><span className="font-medium text-gray-600">Последний вход:</span> {formatDate(userData?.last_login)}</p> */}
                        </div>
                        <div className="mt-6 border-t pt-4">
                            <Button variant="outline" size="sm" onClick={() => setIsEditModalOpen(true)}>Редактировать
                                профиль</Button>
                        </div>
                    </div>
                </div>

                <div className="lg:col-span-2">
                    <h2 className="text-xl font-semibold mb-4">История заказов</h2>
                    {loadingOrders && <LoadingSpinner text="Загрузка заказов..."/>}
                    {!loadingOrders && ordersData.results.length === 0 && (
                        <div className="bg-white p-6 rounded-lg shadow-sm border text-center text-gray-500">У вас пока
                            нет заказов.</div>
                    )}
                    {!loadingOrders && ordersData.results.length > 0 && (
                        <div className="space-y-4">
                            {ordersData.results.map(order => {

                                const calculatedTotalAmount = (order.items || []).reduce((sum, item) => {
                                    const quantity = item?.qty ?? 0;
                                    const pricePerItem = parseFloat(item?.price_per_item ?? 0);
                                    return sum + (quantity * (isNaN(pricePerItem) ? 0 : pricePerItem));
                                }, 0);

                                return (
                                    <div key={order.id} className="bg-white p-4 rounded-lg shadow-sm border">
                                        <div
                                            className="flex flex-wrap justify-between items-center gap-2 mb-3 border-b pb-2">
                                            <h3 className="font-semibold text-lg">
                                                <Link to={`/orders/${order.id}`} className="hover:text-orange-500">Заказ
                                                    №{order.id}</Link>
                                            </h3>
                                            <span
                                                className={`text-xs sm:text-sm px-2 py-0.5 rounded-full whitespace-nowrap ${order.status?.status === 'Доставлен' ? 'bg-green-100 text-green-800' : order.status?.status === 'Отменен' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'}`}>
                                                {order.status?.status || 'Неизвестно'}
                                            </span>
                                            <span
                                                className="text-sm text-gray-500 w-full sm:w-auto text-left sm:text-right mt-1 sm:mt-0">{formatDate(order.order_date)}</span>
                                        </div>
                                        <div className="mb-3 text-sm space-y-1">
                                            <p><span
                                                className="font-medium text-gray-600">Сумма:</span> {formatPrice(calculatedTotalAmount)}
                                            </p> {/* Используем рассчитанную сумму */}
                                            <p><span
                                                className="font-medium text-gray-600">Доставка:</span> {order.delivery_method?.method_name || '-'}
                                            </p>
                                            <p><span
                                                className="font-medium text-gray-600">Оплата:</span> {order.payment?.method_name || '-'}
                                            </p>
                                        </div>
                                        <details className="text-sm">
                                            <summary
                                                className="cursor-pointer text-blue-600 hover:underline font-medium">Показать
                                                товары ({order.items?.length || 0})
                                            </summary>
                                            <ul className="mt-2 space-y-1 pl-4 list-disc list-inside">
                                                {(order.items || []).map(item => (
                                                    <li key={item.id}>
                                                        <Link to={`/products/${item.product}`}
                                                              className='hover:text-orange-500'>{item.product_name || `Товар ID: ${item.product}`}</Link>
                                                        <span
                                                            className='text-gray-600'> - {item.qty} шт. x {formatPrice(item.price_per_item)}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </details>
                                    </div>
                                );
                            })}
                            {(ordersData.next || ordersData.previous) && (
                                <div className="mt-6 flex justify-center items-center gap-4">
                                    <Button onClick={handlePreviousOrders}
                                            disabled={!ordersData.previous || loadingOrders}
                                            variant="outline">Назад</Button>
                                    <Button onClick={handleNextOrders} disabled={!ordersData.next || loadingOrders}
                                            variant="outline">Вперед</Button>
                                </div>
                            )}
                            {ordersData.count > 0 && (
                                <div className="mt-2 text-center text-xs text-gray-500">Всего
                                    заказов: {ordersData.count}</div>
                            )}
                        </div>
                    )}
                </div>
            </div>

            <Modal isOpen={isEditModalOpen} onClose={() => setIsEditModalOpen(false)} title="Редактировать профиль"
                   size="lg">
                <EditProfileForm key={userData?.id} initialData={userData} onSuccess={handleProfileUpdateSuccess}
                                 onCancel={() => setIsEditModalOpen(false)}/>
            </Modal>
        </div>
    );
};

export default ProfilePage;

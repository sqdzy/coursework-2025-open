import React, {useState, useEffect} from 'react';
import {useNavigate} from 'react-router-dom';
import {useAuth} from '../components/context/AuthContext';

import CheckoutStep1 from '../components/checkout/CheckoutStep1';
import CheckoutStep2 from '../components/checkout/CheckoutStep2';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorMessage from '../components/ui/ErrorMessage';
import {createOrder, fetchDeliveryMethods, fetchPaymentMethods} from '../services/api';

const CheckoutPage = () => {
    const {isAuthenticated, isLoading: authLoading, cart, token, clearCartState} = useAuth();
    const navigate = useNavigate();
    const [currentStep, setCurrentStep] = useState(1);
    const [orderDetails, setOrderDetails] = useState({});
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState(null);


    const [deliveryMethods, setDeliveryMethods] = useState([]);
    const [paymentMethods, setPaymentMethods] = useState([]);


    useEffect(() => {
        const loadMethods = async () => {
            try {
                const [deliveryData, paymentData] = await Promise.all([
                    fetchDeliveryMethods(),
                    fetchPaymentMethods()
                ]);
                setDeliveryMethods(deliveryData);
                setPaymentMethods(paymentData);
            } catch (err) {
                console.error("Error pre-loading methods in CheckoutPage:", err);

            }
        };
        loadMethods();
    }, []);


    useEffect(() => {
        if (!authLoading) {
            if (!isAuthenticated) {
                navigate('/auth', {state: {from: {pathname: '/checkout'}}});
            } else if (cart.items.length === 0 && !cart.loading && !cart.error) {
                navigate('/cart');
            }
        }
    }, [isAuthenticated, authLoading, navigate, cart.items.length, cart.loading, cart.error]);


    const handleStep1Submit = (data) => {
        setOrderDetails(data);
        setCurrentStep(2);
        setError(null);
        window.scrollTo(0, 0);
    };


    const handleStep2Back = () => {
        setCurrentStep(1);
        setError(null);
        window.scrollTo(0, 0);
    };


    const handleConfirmOrder = async () => {
        setIsProcessing(true);
        setError(null);
        try {

            const dataToSend = {
                delivery_address: orderDetails.delivery_address,
                contact_phone: orderDetails.contact_phone,
                delivery_method_id: orderDetails.delivery_method_id,
                payment_method_id: orderDetails.payment_method_id,
            };
            console.log("Creating order with data:", dataToSend);
            const createdOrder = await createOrder(dataToSend, token);
            console.log("Order created successfully:", createdOrder);
            clearCartState();

            navigate(`/order-success/${createdOrder.id}`, {replace: true});
        } catch (err) {
            console.error("Failed to create order:", err);
            setError(err.message || 'Не удалось создать заказ. Проверьте данные или попробуйте позже.');

        } finally {
            setIsProcessing(false);
        }
    };


    if (authLoading || (isAuthenticated && cart.loading)) {
        return <div className="container mx-auto px-4 py-10 text-center"><LoadingSpinner text="Загрузка данных..."/>
        </div>;
    }


    if (isAuthenticated && !cart.loading && cart.items.length === 0) {
        return <div className="container mx-auto px-4 py-10 text-center"><ErrorMessage
            message="Ваша корзина пуста. Невозможно оформить заказ."/></div>;
    }


    return (
        <div className="container mx-auto px-4 py-6">
            <h1 className="text-2xl md:text-3xl font-bold mb-6">Оформление заказа</h1>

            {isProcessing && <LoadingSpinner text="Обработка заказа..." className="mb-4"/>}
            {error && <ErrorMessage message={error} className="mb-4"/>}


            <div className="bg-white border rounded-md p-6 shadow-sm">
                {currentStep === 1 && (
                    <CheckoutStep1
                        initialData={orderDetails}
                        onSubmit={handleStep1Submit}
                        onBack={() => navigate('/cart')}
                    />
                )}
                {currentStep === 2 && (
                    <CheckoutStep2
                        orderDetails={orderDetails}
                        deliveryMethods={deliveryMethods}
                        paymentMethods={paymentMethods}
                        onConfirm={handleConfirmOrder}
                        onBack={handleStep2Back}
                        isProcessing={isProcessing}
                    />
                )}
            </div>
        </div>
    );
};

export default CheckoutPage;

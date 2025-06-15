import React from 'react';
import {useParams, Link} from 'react-router-dom';
import Button from '../components/ui/Button';
import {CheckCircle} from 'lucide-react';

const OrderSuccessPage = () => {
    const {orderId} = useParams();

    return (
        <div className="container mx-auto px-4 py-10 text-center">
            <CheckCircle className="mx-auto h-16 w-16 text-green-500 mb-4"/>
            <h1 className="text-2xl md:text-3xl font-bold mb-3">Заказ успешно оформлен!</h1>
            <p className="text-gray-700 mb-2">Спасибо за вашу покупку.</p>
            {orderId && (
                <p className="text-lg font-medium text-gray-800 mb-6">
                    Номер вашего заказа: <span className="text-orange-600">{orderId}</span>
                </p>
            )}
            <p className="text-gray-600 mb-8">
                Мы свяжемся с вами в ближайшее время для подтверждения деталей.
                Вы можете отслеживать статус заказа в вашем личном кабинете (TODO).
            </p>
            <div className="space-x-4">
                <Link to="/orders">
                    <Button variant="outline">Мои заказы</Button>
                </Link>
                <Link to="/">
                    <Button variant="primary">Вернуться на главную</Button>
                </Link>
            </div>
        </div>
    );
};

export default OrderSuccessPage;

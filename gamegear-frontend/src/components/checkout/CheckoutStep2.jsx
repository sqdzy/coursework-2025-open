import React from 'react';
import {useAuth} from '../context/AuthContext';
import Button from '../ui/Button';
import LoadingSpinner from '../ui/LoadingSpinner';


const formatPrice = (price) => new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
}).format(price || 0);

const CheckoutStep2 = ({orderDetails, deliveryMethods, paymentMethods, onConfirm, onBack, isProcessing}) => {
    const {cart} = useAuth();


    const selectedDelivery = deliveryMethods.find(m => String(m.id) === String(orderDetails.delivery_method_id));
    const selectedPayment = paymentMethods.find(m => String(m.id) === String(orderDetails.payment_method_id));


    const cartSubtotal = cart.items.reduce((sum, item) => {

        const itemPrice = parseFloat(item?.total_price ?? 0);

        return sum + (isNaN(itemPrice) ? 0 : itemPrice);
    }, 0);
    const totalCartQuantity = cart.items.reduce((sum, item) => sum + (item?.quantity ?? 0), 0);

    return (
        <div className="space-y-6">
            <h2 className="text-xl font-semibold mb-4">2. Подтверждение заказа</h2>


            <div className="border rounded-md p-4 bg-gray-50 space-y-3">
                <h3 className="font-medium text-lg mb-2">Проверьте данные:</h3>
                <p><span className="font-medium">Телефон:</span> {orderDetails.contact_phone}</p>
                <p><span className="font-medium">Адрес доставки:</span> {orderDetails.delivery_address}</p>
                <p><span className="font-medium">Способ доставки:</span> {selectedDelivery?.method_name || 'Не выбран'}
                </p>
                <p><span className="font-medium">Способ оплаты:</span> {selectedPayment?.method_name || 'Не выбран'}</p>
            </div>


            <div className="border rounded-md p-4 space-y-3">
                <h3 className="font-medium text-lg mb-2">Состав заказа ({totalCartQuantity} шт.):</h3>
                {cart.items.map(item => (
                    <div key={item.id}
                         className="flex justify-between items-center text-sm border-b pb-2 last:border-b-0 last:pb-0">
                        <div className='flex items-center gap-2'>
                            <img
                                src={item.product?.main_image || '/placeholder-image.png'}
                                alt={item.product?.name}
                                className="w-10 h-10 object-contain rounded"
                                onError={(e) => {
                                    e.target.onerror = null;
                                    e.target.src = '/placeholder-image.png';
                                }}
                            />
                            <span>{item.product?.name} <span className="text-gray-500">x {item.quantity}</span></span>
                        </div>
                        <span className="font-medium">{formatPrice(item.total_price)}</span>
                    </div>
                ))}

                <div className="flex justify-end font-bold text-lg pt-3 mt-2">
                    <span>Итого: {formatPrice(cartSubtotal)}</span>
                </div>
            </div>


            <div className="flex justify-between pt-6 border-t">
                <Button type="button" onClick={onBack} variant="outline" disabled={isProcessing}>
                    Назад к данным
                </Button>
                <Button
                    type="button"
                    onClick={onConfirm}
                    variant="primary"
                    disabled={isProcessing}
                    className="min-w-[150px]"
                >
                    {isProcessing ? (
                        <LoadingSpinner text="Оформляем..." className="p-0 inline-flex items-center h-5"/>
                    ) : (
                        `Подтвердить и ${selectedPayment?.method_name?.toLowerCase().includes('онлайн') ? 'оплатить' : 'оформить'}`
                    )}
                </Button>
            </div>

            {selectedPayment?.method_name?.toLowerCase().includes('онлайн') && !isProcessing && (
                <p className="text-xs text-center text-gray-500 mt-4">
                    (Нажимая "Подтвердить и оплатить", вы будете перенаправлены на страницу оплаты - в данном демо заказ
                    будет создан сразу)
                </p>
            )}
        </div>
    );
};

export default CheckoutStep2;

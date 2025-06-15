import React, {useState, useEffect} from 'react';
import {fetchDeliveryMethods, fetchPaymentMethods} from '../../services/api';
import LoadingSpinner from '../ui/LoadingSpinner';
import ErrorMessage from '../ui/ErrorMessage';
import Button from '../ui/Button';

const CheckoutStep1 = ({initialData = {}, onSubmit, onBack}) => {
    const [formData, setFormData] = useState({
        delivery_address: initialData.delivery_address || '',
        contact_phone: initialData.contact_phone || '',
        delivery_method_id: initialData.delivery_method_id || '',
        payment_method_id: initialData.payment_method_id || '',
    });
    const [deliveryMethods, setDeliveryMethods] = useState([]);
    const [paymentMethods, setPaymentMethods] = useState([]);
    const [loadingMethods, setLoadingMethods] = useState(true);
    const [errorMethods, setErrorMethods] = useState(null);
    const [formErrors, setFormErrors] = useState({});


    useEffect(() => {
        const loadMethods = async () => {
            setLoadingMethods(true);
            setErrorMethods(null);
            try {
                const [deliveryData, paymentData] = await Promise.all([
                    fetchDeliveryMethods(),
                    fetchPaymentMethods()
                ]);
                setDeliveryMethods(deliveryData);
                setPaymentMethods(paymentData);

                if (!formData.delivery_method_id && deliveryData.length > 0) {
                    setFormData(prev => ({...prev, delivery_method_id: deliveryData[0].id}));
                }
                if (!formData.payment_method_id && paymentData.length > 0) {
                    setFormData(prev => ({...prev, payment_method_id: paymentData[0].id}));
                }
            } catch (err) {
                setErrorMethods('Не удалось загрузить способы доставки/оплаты.');
                console.error("Error loading checkout methods:", err);
            } finally {
                setLoadingMethods(false);
            }
        };
        loadMethods();
    }, []);

    const handleChange = (e) => {
        const {name, value} = e.target;
        setFormData(prev => ({...prev, [name]: value}));

        if (formErrors[name]) {
            setFormErrors(prev => ({...prev, [name]: undefined}));
        }
    };


    const validateForm = () => {
        const errors = {};
        if (!formData.delivery_address.trim() || formData.delivery_address.length < 10) {
            errors.delivery_address = 'Введите корректный адрес (мин. 10 символов).';
        }

        const phonePattern = /^[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s./0-9]*$/;
        if (!formData.contact_phone.trim() || !phonePattern.test(formData.contact_phone) || formData.contact_phone.length < 7) {
            errors.contact_phone = 'Введите корректный номер телефона.';
        }
        if (!formData.delivery_method_id) {
            errors.delivery_method_id = 'Выберите способ доставки.';
        }
        if (!formData.payment_method_id) {
            errors.payment_method_id = 'Выберите способ оплаты.';
        }
        setFormErrors(errors);
        return Object.keys(errors).length === 0;
    };


    const handleSubmit = (e) => {
        e.preventDefault();
        if (validateForm()) {
            onSubmit(formData);
        } else {
            console.log("Checkout Step 1 validation failed:", formErrors);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            <h2 className="text-xl font-semibold mb-4">1. Данные получателя и доставка</h2>


            <fieldset className="space-y-4">
                <legend className="text-lg font-medium text-gray-900 mb-2">Контактная информация</legend>
                <div>
                    <label htmlFor="contact_phone" className="block text-sm font-medium text-gray-700">
                        Контактный телефон*
                    </label>
                    <input
                        type="tel"
                        id="contact_phone"
                        name="contact_phone"
                        value={formData.contact_phone}
                        onChange={handleChange}
                        required
                        className={`mt-1 block w-full px-3 py-2 border ${formErrors.contact_phone ? 'border-red-500' : 'border-gray-300'} rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm`}
                        placeholder="+7 (XXX) XXX-XX-XX"
                    />
                    {formErrors.contact_phone &&
                        <p className="mt-1 text-xs text-red-600">{formErrors.contact_phone}</p>}
                </div>
                <div>
                    <label htmlFor="delivery_address" className="block text-sm font-medium text-gray-700">
                        Адрес доставки* (Город, улица, дом, квартира)
                    </label>
                    <textarea
                        id="delivery_address"
                        name="delivery_address"
                        rows="3"
                        value={formData.delivery_address}
                        onChange={handleChange}
                        required
                        className={`mt-1 block w-full px-3 py-2 border ${formErrors.delivery_address ? 'border-red-500' : 'border-gray-300'} rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm`}
                        placeholder="г. Москва, ул. Примерная, д. 1, кв. 10"
                    />
                    {formErrors.delivery_address &&
                        <p className="mt-1 text-xs text-red-600">{formErrors.delivery_address}</p>}
                </div>
            </fieldset>


            {loadingMethods && <LoadingSpinner text="Загрузка опций..."/>}
            {errorMethods && <ErrorMessage message={errorMethods}/>}

            {!loadingMethods && !errorMethods && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                    <fieldset>
                        <legend className="text-lg font-medium text-gray-900 mb-2">Способ доставки*</legend>
                        {formErrors.delivery_method_id &&
                            <p className="mb-2 text-xs text-red-600">{formErrors.delivery_method_id}</p>}
                        <div className="space-y-3">
                            {deliveryMethods.map((method) => (
                                <label key={method.id}
                                       className="flex items-center p-3 border rounded-md hover:bg-gray-50 cursor-pointer">
                                    <input
                                        type="radio"
                                        name="delivery_method_id"
                                        value={method.id}
                                        checked={String(formData.delivery_method_id) === String(method.id)}
                                        onChange={handleChange}
                                        required
                                        className="focus:ring-orange-500 h-4 w-4 text-orange-600 border-gray-300"
                                    />
                                    <span className="ml-3 block text-sm font-medium text-gray-700">
                                        {method.method_name}
                                        {method.description &&
                                            <span className="text-xs text-gray-500 block">{method.description}</span>}
                                    </span>
                                </label>
                            ))}
                        </div>
                    </fieldset>


                    <fieldset>
                        <legend className="text-lg font-medium text-gray-900 mb-2">Способ оплаты*</legend>
                        {formErrors.payment_method_id &&
                            <p className="mb-2 text-xs text-red-600">{formErrors.payment_method_id}</p>}
                        <div className="space-y-3">
                            {paymentMethods.map((method) => (
                                <label key={method.id}
                                       className="flex items-center p-3 border rounded-md hover:bg-gray-50 cursor-pointer">
                                    <input
                                        type="radio"
                                        name="payment_method_id"
                                        value={method.id}
                                        checked={String(formData.payment_method_id) === String(method.id)}
                                        onChange={handleChange}
                                        required
                                        className="focus:ring-orange-500 h-4 w-4 text-orange-600 border-gray-300"
                                    />
                                    <span className="ml-3 block text-sm font-medium text-gray-700">
                                        {method.method_name}
                                        {method.description &&
                                            <span className="text-xs text-gray-500 block">{method.description}</span>}
                                    </span>
                                </label>
                            ))}
                        </div>
                    </fieldset>
                </div>
            )}


            <div className="flex justify-between pt-6 border-t">
                <Button type="button" onClick={onBack} variant="outline">
                    Назад в корзину
                </Button>
                <Button type="submit" variant="primary" disabled={loadingMethods}>
                    Перейти к подтверждению
                </Button>
            </div>
        </form>
    );
};

export default CheckoutStep1;

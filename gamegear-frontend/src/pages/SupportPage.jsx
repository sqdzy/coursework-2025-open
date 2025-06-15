import React from 'react';
import {YMaps, Map, Placemark} from '@pbe/react-yandex-maps';
import {Phone, Mail, Send, MessageCircle, MapPin} from 'lucide-react';
import ErrorMessage from "../components/ui/ErrorMessage";


const CONTACTS = {
    phone: '+7 (951) 075-65-20',
    email: 'support@gamegear.ru',
    telegram: 'https://t.me/gamegearshop',
    vk: 'https://vk.com/gamegearshop',
    address: 'г. Москва, ул. Прянишникова, д. 2А,',
    coordinates: [55.833708, 37.543758]
};


const YANDEX_MAPS_API_KEY = process.env.REACT_APP_YANDEX_MAPS_API_KEY;


const ContactItem = ({icon, label, value, href}) => (
    <a
        href={href || '#'}
        target={href && href.startsWith('http') ? '_blank' : undefined}
        rel="noopener noreferrer"
        className="flex items-center gap-3 p-3 rounded-lg transition-colors duration-200 hover:bg-gray-100 group"
    >
        <div className="flex-shrink-0 text-orange-500 group-hover:text-orange-600">
            {icon}
        </div>
        <div>
            <div className="text-sm font-medium text-gray-500 group-hover:text-gray-600">{label}</div>
            <div className="text-base font-semibold text-gray-800 group-hover:text-orange-600">{value}</div>
        </div>
    </a>
);


const SupportPage = () => {

    if (!YANDEX_MAPS_API_KEY) {
        console.error("Yandex Maps API Key is not configured in .env file (REACT_APP_YANDEX_MAPS_API_KEY)");

        return (
            <div className="container mx-auto px-4 py-10 text-center">
                <ErrorMessage message="Ошибка конфигурации: Ключ API Яндекс Карт не найден."/>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8 md:py-12">
            <h1 className="text-3xl md:text-4xl font-bold mb-8 text-center text-gray-800">
                Поддержка клиентов
            </h1>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">


                <div className="bg-white p-6 rounded-lg shadow-md border">
                    <h2 className="text-2xl font-semibold mb-6 text-gray-700">Свяжитесь с нами</h2>
                    <div className="space-y-4">
                        <ContactItem
                            icon={<Phone size={24}/>}
                            label="Телефон"
                            value={CONTACTS.phone}
                            href={`tel:${CONTACTS.phone.replace(/[\s()-]/g, '')}`}
                        />
                        <ContactItem
                            icon={<Mail size={24}/>}
                            label="Email"
                            value={CONTACTS.email}
                            href={`mailto:${CONTACTS.email}`}
                        />
                        <ContactItem
                            icon={<Send size={24}/>}
                            label="Telegram"
                            value="@gamegearshop"
                            href={CONTACTS.telegram}
                        />
                        <ContactItem
                            icon={<MessageCircle size={24}/>}
                            label="ВКонтакте"
                            value="gamegearshop"
                            href={CONTACTS.vk}
                        />
                    </div>
                    <p className="mt-6 text-sm text-gray-500">
                        Мы работаем для вас с 10:00 до 20:00 по московскому времени, без выходных.
                    </p>
                </div>


                <div className="bg-white p-6 rounded-lg shadow-md border">
                    <h2 className="text-2xl font-semibold mb-4 text-gray-700">Наш адрес</h2>
                    <div className="flex items-start gap-3 mb-4">
                        <MapPin size={24} className="flex-shrink-0 text-orange-500 mt-1"/>
                        <p className="text-base text-gray-800 font-medium">
                            {CONTACTS.address}
                        </p>
                    </div>


                    <div className="w-full h-64 md:h-80 rounded-lg overflow-hidden border">
                        <YMaps query={{apikey: YANDEX_MAPS_API_KEY, lang: 'ru_RU'}}>
                            <Map
                                defaultState={{
                                    center: CONTACTS.coordinates,
                                    zoom: 16,
                                }}
                                width="100%"
                                height="100%"
                            >
                                <Placemark
                                    geometry={CONTACTS.coordinates}
                                    properties={{
                                        balloonContentHeader: 'Магазин GameGear',
                                        balloonContentBody: CONTACTS.address,
                                        hintContent: 'GameGear - Мы здесь!',
                                    }}
                                    options={{
                                        preset: 'islands#orangeDotIcon',
                                    }}
                                />
                            </Map>
                        </YMaps>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SupportPage;

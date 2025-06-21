import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../components/context/AuthContext';
import axios from 'axios';

const SocialAuthCallback = () => {
    const navigate = useNavigate();
    const { setupStateAndFetchCart } = useAuth();

    useEffect(() => {
        const getToken = async () => {
            try {
                const response = await axios.get('https://api-gg.familycore.ru/api/auth/get-token/', {
                    withCredentials: true,
                });

                const { token, user } = response.data;

                if (token && user) {
                    await setupStateAndFetchCart(token, user);
                    navigate('/');
                } else {
                    throw new Error('Не удалось получить токен от бэкенда.');
                }
            } catch (error) {
                console.error("Ошибка при получении токена после соц. входа:", error);
                navigate('/login');
            }
        };

        getToken();
    }, [navigate, setupStateAndFetchCart]);

    return (
        <div className="flex justify-center items-center h-screen">
            <p className="text-xl">Завершение входа, пожалуйста, подождите...</p>
        </div>
    );
};

export default SocialAuthCallback;
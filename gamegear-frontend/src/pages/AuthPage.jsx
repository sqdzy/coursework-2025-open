import React, {useState, useEffect} from 'react';
import {useAuth} from '../components/context/AuthContext';
import {useNavigate, useLocation} from 'react-router-dom';
import {useGoogleLogin} from '@react-oauth/google';
import Button from '../components/ui/Button';

const AuthPage = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);
    const {login, loginWithGoogle, isAuthenticated, isLoading} = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const from = location.state?.from?.pathname || "/";

    useEffect(() => {
        if (isAuthenticated) {
            navigate(from, {replace: true});
        }
    }, [isAuthenticated, navigate, from]);

    const handleGoogleLoginSuccess = async (tokenResponse) => {

        const result = await loginWithGoogle(tokenResponse.access_token);
        if (!result.success) {
            setError(result.error);
        }
    };

    const googleLogin = useGoogleLogin({
        onSuccess: handleGoogleLoginSuccess,
        onError: () => setError('Не удалось войти с помощью Google.'),

    });

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        if (!username || !password) {
            setError("Введите имя пользователя и пароль.");
            return;
        }
        const result = await login(username, password);
        if (!result.success) {
            setError(result.error || 'Произошла неизвестная ошибка.');
        }
    };

    return (
        <div className="flex justify-center items-center py-12 px-4 min-h-[calc(100vh-200px)]">
            <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md">
                <h2 className="text-2xl font-bold text-center text-gray-900">Вход или Регистрация</h2>
                <form className="space-y-6" onSubmit={handleSubmit}>
                    {error && (
                        <div
                            className="p-3 bg-red-100 border border-red-300 text-red-700 text-sm rounded-md">{error}</div>
                    )}
                    <div>
                        <label htmlFor="username" className="block text-sm font-medium text-gray-700">Имя
                            пользователя</label>
                        <input id="username" name="username" type="text" autoComplete="username" required
                               className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm disabled:bg-gray-100"
                               value={username} onChange={(e) => setUsername(e.target.value)} disabled={isLoading}
                               placeholder="Введите ваш логин"/>
                    </div>
                    <div>
                        <label htmlFor="password" className="block text-sm font-medium text-gray-700">Пароль</label>
                        <input id="password" name="password" type="password" autoComplete="current-password" required
                               className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm disabled:bg-gray-100"
                               value={password} onChange={(e) => setPassword(e.target.value)} disabled={isLoading}
                               placeholder="Введите ваш пароль"/>
                    </div>
                    <div>
                        <Button type="submit" className="w-full" disabled={isLoading} variant="primary">
                            {isLoading ? 'Обработка...' : 'Войти / Зарегистрироваться'}
                        </Button>
                    </div>
                </form>
                <div className="relative flex py-3 items-center">
                    <div className="flex-grow border-t border-gray-300"></div>
                    <span className="flex-shrink mx-4 text-gray-500 text-sm">или</span>
                    <div className="flex-grow border-t border-gray-300"></div>
                </div>
                <Button onClick={() => googleLogin()}
                        className="w-full bg-white border-gray-300 border text-gray-700 hover:bg-gray-50 flex items-center justify-center"
                        variant="secondary" disabled={isLoading}>
                    <img src="https://www.google.com/favicon.ico" alt="Google icon" className="w-5 h-5 mr-2"/>
                    Войти через Google
                </Button>
            </div>
        </div>
    );
};

export default AuthPage;
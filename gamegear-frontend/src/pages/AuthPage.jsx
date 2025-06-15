import React, {useState} from 'react';
import {useAuth} from '../components/context/AuthContext';
import {useNavigate, Link, useLocation} from 'react-router-dom';
import Button from '../components/ui/Button';

const AuthPage = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    const {login, isAuthenticated} = useAuth();
    const navigate = useNavigate();
    const location = useLocation();


    const from = location.state?.from?.pathname || "/";


    React.useEffect(() => {
        if (isAuthenticated) {
            console.log("Already authenticated, redirecting to", from);
            navigate(from, {replace: true});
        }
    }, [isAuthenticated, navigate, from]);


    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        if (!username || !password) {
            setError("Введите имя пользователя и пароль.");
            setLoading(false);
            return;
        }

        const result = await login(username, password);

        setLoading(false);
        if (result.success) {
            console.log("Auth successful, navigating to", from);
            navigate(from, {replace: true});
        } else {
            setError(result.error || 'Произошла неизвестная ошибка.');
        }
    };

    return (
        <div className="flex justify-center items-center py-12 px-4 min-h-[calc(100vh-200px)]">
            <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md">
                <h2 className="text-2xl font-bold text-center text-gray-900">
                    Вход или Регистрация
                </h2>
                <form className="space-y-6" onSubmit={handleSubmit}>
                    {error && (
                        <div className="p-3 bg-red-100 border border-red-300 text-red-700 text-sm rounded-md">
                            {error}
                        </div>
                    )}
                    <div>
                        <label
                            htmlFor="username"
                            className="block text-sm font-medium text-gray-700"
                        >
                            Имя пользователя
                        </label>
                        <input
                            id="username"
                            name="username"
                            type="text"
                            autoComplete="username"
                            required
                            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm disabled:bg-gray-100"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            disabled={loading}
                            placeholder="Введите ваш логин"
                        />
                    </div>
                    <div>
                        <label
                            htmlFor="password"
                            className="block text-sm font-medium text-gray-700"
                        >
                            Пароль
                        </label>
                        <input
                            id="password"
                            name="password"
                            type="password"
                            autoComplete="current-password"
                            required
                            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm disabled:bg-gray-100"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            disabled={loading}
                            placeholder="Введите ваш пароль"
                        />
                    </div>

                    <div>
                        <Button
                            type="submit"
                            className="w-full"
                            disabled={loading}
                            variant="primary"
                        >
                            {loading ? 'Обработка...' : 'Войти / Зарегистрироваться'}
                        </Button>
                    </div>
                </form>

            </div>
        </div>
    );
};

export default AuthPage;

import React, {createContext, useState, useContext, useEffect, useCallback} from 'react';
import { loginOrRegisterUser, fetchCartItems, addCartItem, updateCartItem, deleteCartItem } from '../../services/api';
import axios from 'axios';

export const AuthContext = createContext(null);
const API_BASE_URL = 'https://api-gg.familycore.ru/api';

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({children}) => {
    const [authState, setAuthState] = useState({
        token: null, user: null, isAuthenticated: false, isLoading: true,
        cart: { items: [], loading: false, error: null }
    });

    const clearStateAndStorage = useCallback(() => {
        localStorage.removeItem('authToken');
        localStorage.removeItem('authUser');
        setAuthState({
            token: null, user: null, isAuthenticated: false, isLoading: false,
            cart: { items: [], loading: false, error: null }
        });
    }, []);

    const fetchCart = useCallback(async (currentToken) => {
        if (!currentToken) {
            setAuthState(prev => ({ ...prev, cart: { items: [], loading: false, error: null } }));
            return;
        }
        setAuthState(prev => ({ ...prev, cart: { ...prev.cart, loading: true, error: null } }));
        try {
            const cartData = await fetchCartItems(currentToken);
            setAuthState(prev => ({ ...prev, cart: { items: Array.isArray(cartData) ? cartData : (cartData?.results || []), loading: false, error: null } }));
        } catch (error) {
            setAuthState(prev => ({ ...prev, cart: { ...prev.cart, loading: false, error: error.message || 'Не удалось загрузить корзину' } }));
        }
    }, []);

    const setupStateAndFetchCart = useCallback(async (token, user) => {
        localStorage.setItem('authToken', token);
        localStorage.setItem('authUser', JSON.stringify(user));
        setAuthState({
            token: token, user: user, isAuthenticated: true, isLoading: false,
            cart: { items: [], loading: true, error: null }
        });
        await fetchCart(token);
    }, [fetchCart]);

    const login = useCallback(async (username, password) => {
        setAuthState(prev => ({...prev, isLoading: true}));
        try {
            const data = await loginOrRegisterUser(username, password);
            const { token, user_id, username_out } = data;
            const userData = { id: user_id, username: username_out };
            await setupStateAndFetchCart(token, userData);
            return { success: true, user: userData };
        } catch (error) {
            clearStateAndStorage();
            return { success: false, error: error.message || 'Ошибка входа/регистрации' };
        } finally {
            setAuthState(prev => ({ ...prev, isLoading: false }));
        }
    }, [setupStateAndFetchCart, clearStateAndStorage]);

    const loginWithGoogle = useCallback(async (accessToken) => {
        setAuthState(prev => ({...prev, isLoading: true}));
        try {
            const response = await axios.post(`${API_BASE_URL}/auth/google/login/`, { access_token: accessToken });
            const { token, user } = response.data;
            await setupStateAndFetchCart(token, user);
            return { success: true };
        } catch (error) {
            clearStateAndStorage();
            const errorMessage = error.response?.data?.detail || 'Ошибка входа через Google.';
            return { success: false, error: errorMessage };
        } finally {
            setAuthState(prev => ({ ...prev, isLoading: false }));
        }
    }, [setupStateAndFetchCart, clearStateAndStorage]);

    const logout = useCallback(() => {
        clearStateAndStorage();
    }, [clearStateAndStorage]);

    useEffect(() => {
        const token = localStorage.getItem('authToken');
        const user = JSON.parse(localStorage.getItem('authUser'));
        if (token && user) {
            setupStateAndFetchCart(token, user);
        } else {
            setAuthState(prev => ({...prev, isLoading: false }));
        }
    }, [setupStateAndFetchCart]);

    const addToCart = useCallback(async (productId, quantity = 1) => {
        const currentToken = authState.token;
        if (!currentToken) throw new Error("Необходима авторизация");
        setAuthState(prev => ({...prev, cart: {...prev.cart, loading: true}}));
        try {
            await addCartItem(productId, quantity, currentToken);
            await fetchCart(currentToken);
            return {success: true};
        } catch (error) {
            setAuthState(prev => ({...prev, cart: {...prev.cart, loading: false, error: error.message}}));
            return {success: false, error: error.message};
        }
    }, [authState.token, fetchCart]);

    const updateCartQuantity = useCallback(async (cartItemId, quantity) => {
        const currentToken = authState.token;
        if (!currentToken) throw new Error("Необходима авторизация");

        if (quantity < 1) {
            return await removeFromCart(cartItemId);
        }

        setAuthState(prev => ({...prev, cart: {...prev.cart, loading: true}}));
        try {
            await updateCartItem(cartItemId, quantity, currentToken);
            await fetchCart(currentToken);
            return {success: true};
        } catch (error) {
            setAuthState(prev => ({...prev, cart: {...prev.cart, loading: false, error: error.message}}));
            return {success: false, error: error.message};
        }
    }, [authState.token, fetchCart]);

    const removeFromCart = useCallback(async (cartItemId) => {
        const currentToken = authState.token;
        if (!currentToken) throw new Error("Необходима авторизация");

        setAuthState(prev => ({...prev, cart: {...prev.cart, loading: true}}));
        try {
            await deleteCartItem(cartItemId, currentToken);
            await fetchCart(currentToken);
            return {success: true};
        } catch (error) {
            setAuthState(prev => ({...prev, cart: {...prev.cart, loading: false, error: error.message}}));
            return {success: false, error: error.message};
        }
    }, [authState.token, fetchCart]);

    const clearCartState = useCallback(() => {
        setAuthState(prev => ({
            ...prev,
            cart: {items: [], loading: false, error: null}
        }));
    }, []);

    const value = {
        ...authState,
        login,
        logout,
        loginWithGoogle,
        fetchCart: () => fetchCart(authState.token),
        addToCart,
        updateCartQuantity,
        removeFromCart,
        clearCartState,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
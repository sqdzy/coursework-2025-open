import React, {createContext, useState, useContext, useEffect, useCallback} from 'react';

import {
    loginOrRegisterUser,
    fetchCartItems,
    addCartItem,
    updateCartItem,
    deleteCartItem
} from '../../services/api';


const AuthContext = createContext(null);


export const useAuth = () => useContext(AuthContext);


export const AuthProvider = ({children}) => {
    const [authState, setAuthState] = useState({
        token: null,
        user: null,
        isAuthenticated: false,
        isLoading: true,

        cart: {
            items: [],
            loading: false,
            error: null,
        }

    });


    const fetchCart = useCallback(async (currentToken) => {

        if (!currentToken) {
            console.log("fetchCart: No token provided, skipping fetch.");

            setAuthState(prev => ({
                ...prev,
                cart: {items: [], loading: false, error: null}
            }));
            return;
        }

        console.log("fetchCart: Fetching cart items...");
        setAuthState(prev => ({
            ...prev,
            cart: {...prev.cart, loading: true, error: null}
        }));
        try {
            const cartData = await fetchCartItems(currentToken);
            setAuthState(prev => ({
                ...prev,
                cart: {
                    items: Array.isArray(cartData) ? cartData : (cartData?.results || []),
                    loading: false,
                    error: null
                }
            }));
            console.log("Cart fetched:", cartData);
        } catch (error) {
            console.error("Failed to fetch cart:", error);
            setAuthState(prev => ({
                ...prev,
                cart: {...prev.cart, loading: false, error: error.message || 'Не удалось загрузить корзину'}
            }));
        }
    }, []);


    const addToCart = useCallback(async (productId, quantity = 1) => {
        const currentToken = authState.token;
        if (!currentToken) throw new Error("Необходима авторизация");

        console.log(`addToCart: Adding product ${productId}, quantity ${quantity}`);
        setAuthState(prev => ({...prev, cart: {...prev.cart, loading: true}}));
        try {
            await addCartItem(productId, quantity, currentToken);
            await fetchCart(currentToken);
            return {success: true};
        } catch (error) {
            console.error("Failed to add item to cart:", error);
            setAuthState(prev => ({...prev, cart: {...prev.cart, loading: false, error: error.message}}));
            return {success: false, error: error.message};
        } finally {


        }
    }, [authState.token, fetchCart]);


    const updateCartQuantity = useCallback(async (cartItemId, quantity) => {
        const currentToken = authState.token;
        if (!currentToken) throw new Error("Необходима авторизация");

        console.log(`updateCartQuantity: Updating item ${cartItemId} to quantity ${quantity}`);

        if (quantity < 1) {
            console.warn("Attempted to update quantity to less than 1. Removing item instead.");
            return await removeFromCart(cartItemId);
        }

        setAuthState(prev => ({...prev, cart: {...prev.cart, loading: true}}));
        try {
            await updateCartItem(cartItemId, quantity, currentToken);
            await fetchCart(currentToken);
            return {success: true};
        } catch (error) {
            console.error("Failed to update cart item quantity:", error);
            setAuthState(prev => ({...prev, cart: {...prev.cart, loading: false, error: error.message}}));
            return {success: false, error: error.message};
        }
    }, [authState.token, fetchCart]);


    const removeFromCart = useCallback(async (cartItemId) => {
        const currentToken = authState.token;
        if (!currentToken) throw new Error("Необходима авторизация");

        console.log(`removeFromCart: Removing item ${cartItemId}`);
        setAuthState(prev => ({...prev, cart: {...prev.cart, loading: true}}));
        try {
            await deleteCartItem(cartItemId, currentToken);
            await fetchCart(currentToken);
            return {success: true};
        } catch (error) {
            console.error("Failed to remove item from cart:", error);
            setAuthState(prev => ({...prev, cart: {...prev.cart, loading: false, error: error.message}}));
            return {success: false, error: error.message};
        }
    }, [authState.token, fetchCart]);


    const login = useCallback(async (username, password) => {
        console.log(`login: Attempting login/register for ${username}`);

        setAuthState({
            token: null, user: null, isAuthenticated: false, isLoading: true,
            cart: {items: [], loading: false, error: null}
        });
        try {
            const data = await loginOrRegisterUser(username, password);
            const {token, user_id, username_out} = data;
            const userData = {id: user_id, username: username_out};

            localStorage.setItem('authToken', token);
            localStorage.setItem('authUser', JSON.stringify(userData));


            setAuthState({
                token: token,
                user: userData,
                isAuthenticated: true,
                isLoading: false,
                cart: {items: [], loading: true, error: null}
            });
            console.log("Login/Register successful:", userData);
            await fetchCart(token);
            return {success: true, user: userData};
        } catch (error) {
            console.error("Login/Register failed:", error);
            localStorage.removeItem('authToken');
            localStorage.removeItem('authUser');
            setAuthState({
                token: null,
                user: null,
                isAuthenticated: false,
                isLoading: false,
                cart: {items: [], loading: false, error: null}
            });
            return {success: false, error: error.message || 'Ошибка входа/регистрации'};
        }
    }, [fetchCart]);

    const clearCartState = useCallback(() => {
        console.log("clearCartState: Clearing cart state locally.");
        setAuthState(prev => ({
            ...prev,
            cart: {items: [], loading: false, error: null}
        }));
    }, []);


    const logout = useCallback(() => {
        console.log("logout: Logging out user");
        localStorage.removeItem('authToken');
        localStorage.removeItem('authUser');

        setAuthState({
            token: null,
            user: null,
            isAuthenticated: false,
            isLoading: false,
            cart: {items: [], loading: false, error: null}
        });
        console.log("User logged out, state cleared");


    }, []);


    useEffect(() => {
        console.log("AuthProvider: Initializing state...");
        const token = localStorage.getItem('authToken');
        const user = JSON.parse(localStorage.getItem('authUser'));
        if (token && user) {
            console.log("AuthProvider: Found token and user in localStorage. Setting initial state.");

            setAuthState({
                token: token,
                user: user,
                isAuthenticated: true,
                isLoading: false,
                cart: {items: [], loading: true, error: null}
            });

            fetchCart(token);
        } else {
            console.log("AuthProvider: No token/user found in localStorage.");

            setAuthState(prev => ({...prev, isLoading: false}));
        }

    }, []);


    const value = {
        ...authState,
        login,
        logout,
        fetchCart: () => fetchCart(authState.token),
        addToCart,
        updateCartQuantity,
        removeFromCart,
        clearCartState,
    };


    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};


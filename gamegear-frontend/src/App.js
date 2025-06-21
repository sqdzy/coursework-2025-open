import React from 'react';
import {BrowserRouter as Router, Route, Routes, useParams} from 'react-router-dom';
import {GoogleOAuthProvider} from '@react-oauth/google';

import HomePage from './pages/HomePage';
import ProductPage from './pages/ProductPage';
import Layout from './components/layout/Layout';
import CategoryPage from "./pages/CategoryPage";
import {AuthProvider} from "./components/context/AuthContext";
import AuthPage from "./pages/AuthPage";
import CartPage from "./pages/CartPage";
import CatalogPage from "./pages/CatalogPage";
import CheckoutPage from "./pages/CheckoutPage";
import OrderSuccessPage from "./pages/OrderSuccessPage";
import ProfilePage from "./pages/ProfilePage";
import SupportPage from './pages/SupportPage';
import PromotionsPage from "./pages/PromotionsPage";

const GOOGLE_CLIENT_ID = '826017848647-s7dt977mv6om91qpvt3cjkmfcam0ebqo.apps.googleusercontent.com';

function App() {
    return (
        <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
            <AuthProvider>
                <Router>
                    <Layout>
                        <Routes>
                            <Route path="/" element={<HomePage/>}/>
                            <Route path="/products/:productId" element={<ProductPageLoader/>}/>
                            <Route path="/categories/:categoryId" element={<CategoryPage/>}/>
                            <Route path="/auth" element={<AuthPage/>}/>
                            <Route path="/cart" element={<CartPage/>}/>
                            <Route path="/catalog" element={<CatalogPage/>}/>
                            <Route path="/checkout" element={<CheckoutPage/>}/>
                            <Route path="/order-success/:orderId" element={<OrderSuccessPage/>}/>
                            <Route path="/profile" element={<ProfilePage/>}/>
                            <Route path="/support" element={<SupportPage/>}/>
                            <Route path="/promotions" element={<PromotionsPage/>}/>
                            <Route path="*" element={<NotFound/>}/>
                        </Routes>
                    </Layout>
                </Router>
            </AuthProvider>
        </GoogleOAuthProvider>
    );
}

const ProductPageLoader = () => {
    const {productId} = useParams();
    return <ProductPage productId={productId}/>;
};

const NotFound = () => (
    <div className="text-center py-10">
        <h1 className="text-3xl font-bold mb-4">404 - Страница не найдена</h1>
        <p className="text-gray-600">Извините, страница, которую вы ищете, не существует.</p>
        <a href="/" className="text-orange-500 hover:underline mt-4 inline-block">На главную</a>
    </div>
);

export default App;
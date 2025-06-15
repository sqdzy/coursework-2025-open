import React from 'react';
import { User, HeartHandshake, ShoppingCart, LogOut, LogIn } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Navbar = ({ isMobileLayout = false, closeMobileMenu = () => {} }) => {
    const { isAuthenticated, user, logout, isLoading: authLoading, cart } = useAuth();
    const navigate = useNavigate();

    const totalCartQuantity = cart.items.reduce((sum, item) => sum + (item?.quantity || 0), 0);

    const handleLogout = () => {
        logout();
        closeMobileMenu();
        navigate('/');
    };

    const handleAuthClick = () => {
        closeMobileMenu();
        navigate('/auth');
    };

    const handleProfileClick = () => {
        closeMobileMenu();
        navigate('/profile');
    };

    const handleSupportClick = () => {
        closeMobileMenu();
        navigate('/support');
    };

    const handleCartClick = () => {
        closeMobileMenu();
        navigate('/cart');
    };

    return (
        <nav className={`flex ${isMobileLayout ? 'flex-col space-y-2 items-stretch' : 'items-center gap-5 md:gap-6'}`}>
            {authLoading ? (
                <div className={`flex items-center ${isMobileLayout ? 'p-2 w-full justify-start' : 'flex-col'}`}>
                    <div className={`bg-gray-200 rounded-full animate-pulse ${isMobileLayout ? 'h-6 w-6 mr-2' : 'h-6 w-6 mb-1'}`}></div>
                    <div className={`bg-gray-200 rounded animate-pulse ${isMobileLayout ? 'h-4 w-20' : 'h-3 w-10'}`}></div>
                </div>
            ) : isAuthenticated && user ? (
                <>
                    <NavItemButton
                        onClick={handleProfileClick}
                        icon={<User size={isMobileLayout ? 20 : 24} />}
                        label={user.username}
                        isMobileLayout={isMobileLayout}
                        title="Перейти в профиль"
                    />
                    <NavItemButton
                        onClick={handleLogout}
                        icon={<LogOut size={isMobileLayout ? 20 : 24} />}
                        label="Выйти"
                        isMobileLayout={isMobileLayout}
                        title="Выйти"
                        className="text-red-600 hover:bg-red-50 hover:text-red-700"
                    />
                </>
            ) : (
                <NavItemButton
                    onClick={handleAuthClick}
                    icon={<LogIn size={isMobileLayout ? 20 : 24} />}
                    label="Войти"
                    isMobileLayout={isMobileLayout}
                />
            )}

            <NavItemButton
                onClick={handleSupportClick}
                icon={<HeartHandshake size={isMobileLayout ? 20 : 24} />}
                label="Поддержка"
                isMobileLayout={isMobileLayout}
            />
            <NavItemButton
                onClick={handleCartClick}
                icon={<ShoppingCart size={isMobileLayout ? 20 : 24} />}
                label="Корзина"
                badgeCount={isAuthenticated ? totalCartQuantity : 0}
                isMobileLayout={isMobileLayout}
            />
        </nav>
    );
};

const NavItemButton = ({ icon, label, onClick, badgeCount, isMobileLayout, className = '', title = '' }) => {
    const IconComponent = React.cloneElement(icon, {
        className: `${icon.props.className || ''} flex-shrink-0 ${isMobileLayout ? 'mr-2' : ''}`
    });

    return (
        <button
            onClick={onClick}
            title={title || label}
            className={`relative flex items-center gap-2 p-2 rounded-md text-gray-600 hover:bg-gray-100 hover:text-orange-600 transition-colors duration-150 ${isMobileLayout ? 'w-full justify-start text-left' : 'flex-col text-center'} ${className}`}
        >
            {IconComponent}
            <span className={`${isMobileLayout ? 'text-sm' : 'text-xs mt-0.5'}`}>{label}</span>
            {badgeCount > 0 && (
                <span
                    className="absolute top-0 right-0 md:top-[-4px] md:right-[-4px] inline-flex items-center justify-center px-1.5 h-4 text-[10px] font-bold leading-none text-red-100 bg-red-600 rounded-full"
                >
                    {badgeCount > 9 ? '9+' : badgeCount}
                </span>
            )}
        </button>
    );
};

export default Navbar;
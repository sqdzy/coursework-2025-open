import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../navigation/Navbar';
import Searchbar from '../navigation/Searchbar';
import { Menu as MenuIcon, X as CloseIcon } from 'lucide-react';

const Header = () => {
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    useEffect(() => {
        const handleResize = () => {
            if (window.innerWidth >= 768) { // md breakpoint
                setIsMobileMenuOpen(false);
            }
        };
        window.addEventListener('resize', handleResize);
        handleResize();
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const toggleMobileMenu = () => {
        setIsMobileMenuOpen(!isMobileMenuOpen);
    };

    return (
        <header className="w-full py-3 px-4 sm:px-6 bg-white shadow-sm sticky top-0 z-50">
            <div className="container mx-auto flex items-center justify-between">
                <div className="flex items-center flex-shrink-0">
                    <Link to="/" className="mr-4 md:mr-6">
                        <h1 className="font-bold text-lg sm:text-xl text-orange-500 hover:text-orange-600">GAMEGEAR</h1>
                        <p className="text-xs text-gray-500 hidden sm:block">игровая периферия</p>
                    </Link>
                </div>

                <div className="hidden md:flex flex-1 max-w-md lg:max-w-xl mx-4">
                    <Searchbar />
                </div>

                <div className="hidden md:flex items-center">
                    <Navbar />
                </div>

                <div className="md:hidden">
                    <button
                        onClick={toggleMobileMenu}
                        className="p-2 rounded-md text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-orange-500"
                        aria-expanded={isMobileMenuOpen}
                        aria-controls="mobile-menu-header"
                    >
                        <span className="sr-only">Открыть главное меню</span>
                        {isMobileMenuOpen ? <CloseIcon size={24} /> : <MenuIcon size={24} />}
                    </button>
                </div>
            </div>

            <div
                id="mobile-menu-header"
                className={`md:hidden absolute top-full left-0 right-0 bg-white shadow-lg z-40 transition-all duration-300 ease-in-out transform ${
                    isMobileMenuOpen ? 'max-h-screen opacity-100 translate-y-0' : 'max-h-0 opacity-0 -translate-y-4 pointer-events-none'
                } overflow-hidden`}
            >
                <div className="px-4 pt-3 pb-4 space-y-4">
                    <div className="mb-3">
                        <Searchbar />
                    </div>
                    <div className="border-t pt-3">
                        <Navbar isMobileLayout={true} closeMobileMenu={() => setIsMobileMenuOpen(false)} />
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;
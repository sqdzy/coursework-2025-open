import React, {useState, useEffect, useRef, useCallback} from 'react';
import {Search, X as CloseIcon} from 'lucide-react';
import {Link, useNavigate} from 'react-router-dom';
import {fetchSearchSuggestions} from '../../services/api';
import {useDebounce} from '../../hooks/useDebounce';

const PLACEHOLDER_IMAGE = '/placeholder-image.png';

const Searchbar = () => {
    const [query, setQuery] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isFocused, setIsFocused] = useState(false);
    const navigate = useNavigate();
    const searchContainerRef = useRef(null);


    const debouncedQuery = useDebounce(query, 300);


    const loadSuggestions = useCallback(async (searchQuery) => {
        if (!searchQuery || searchQuery.trim().length < 2) {
            setSuggestions([]);
            setIsLoading(false);
            return;
        }
        setIsLoading(true);
        try {
            const results = await fetchSearchSuggestions(searchQuery);
            setSuggestions(results);
        } catch (error) {

            setSuggestions([]);
        } finally {
            setIsLoading(false);
        }
    }, []);


    useEffect(() => {
        loadSuggestions(debouncedQuery);
    }, [debouncedQuery, loadSuggestions]);


    const handleSearchSubmit = (e) => {
        e.preventDefault();
        if (query.trim()) {
            setSuggestions([]);
            setIsFocused(false);

            navigate(`/catalog?search=${encodeURIComponent(query.trim())}`);
            console.log('Navigating to search results for:', query.trim());
        }
    };


    const handleInputChange = (e) => {
        setQuery(e.target.value);
    };


    const handleSuggestionClick = () => {
        setSuggestions([]);
        setIsFocused(false);
        setQuery('');
    };


    const handleClearInput = () => {
        setQuery('');
        setSuggestions([]);
        setIsLoading(false);

        searchContainerRef.current?.querySelector('input')?.focus();
    };


    useEffect(() => {
        const handleClickOutside = (event) => {
            if (searchContainerRef.current && !searchContainerRef.current.contains(event.target)) {
                setIsFocused(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);


    const showSuggestions = isFocused && (query.length > 0);

    return (

        <div ref={searchContainerRef} className="relative flex-1 max-w-xs sm:max-w-md md:max-w-lg lg:max-w-xl mx-4">
            <form onSubmit={handleSearchSubmit} className="relative">
                <input
                    type="text"
                    placeholder="Поиск по товарам..."
                    value={query}
                    onChange={handleInputChange}
                    onFocus={() => setIsFocused(true)}
                    className="w-full border border-gray-300 rounded-md py-2 pl-4 pr-16 focus:outline-none focus:ring-1 focus:ring-orange-500 focus:border-orange-500 transition"
                    aria-label="Поиск по товарам"
                />

                {query && (
                    <button
                        type="button"
                        onClick={handleClearInput}
                        className="absolute right-10 top-1/2 transform -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600"
                        aria-label="Очистить поиск"
                    >
                        <CloseIcon size={18}/>
                    </button>
                )}

                <button
                    type="submit"
                    className="absolute right-0 top-0 bottom-0 px-3 flex items-center text-gray-400 hover:text-orange-500"
                    aria-label="Найти"
                >
                    {isLoading ? (
                        <div
                            className="w-5 h-5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                    ) : (
                        <Search size={20}/>
                    )}
                </button>
            </form>


            {showSuggestions && (
                <div
                    className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-md shadow-lg z-50 max-h-96 overflow-y-auto">
                    {isLoading && query.length >= 2 && (
                        <div className="p-4 text-center text-gray-500">
                            <div
                                className="w-5 h-5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin mx-auto"></div>
                        </div>
                    )}
                    {!isLoading && suggestions.length === 0 && debouncedQuery.length >= 2 && (
                        <div className="p-4 text-center text-gray-500 text-sm">
                            По запросу "{debouncedQuery}" ничего не найдено.
                        </div>
                    )}
                    {!isLoading && suggestions.length > 0 && (
                        <ul>
                            {suggestions.map((product) => (
                                <li key={product.id}>
                                    <Link
                                        to={`/products/${product.id}`}
                                        onClick={handleSuggestionClick}
                                        className="flex items-center gap-3 px-4 py-2 hover:bg-gray-100 cursor-pointer"
                                    >
                                        <img
                                            src={product.main_image || PLACEHOLDER_IMAGE}
                                            alt={product.name}
                                            className="w-10 h-10 object-contain flex-shrink-0 bg-gray-50 rounded"
                                            onError={(e) => {
                                                e.target.onerror = null;
                                                e.target.src = PLACEHOLDER_IMAGE;
                                            }}
                                        />
                                        <div className="flex-grow min-w-0">
                                            <p className="text-sm font-medium text-gray-800 truncate">
                                                {product.name}
                                            </p>


                                        </div>
                                    </Link>
                                </li>
                            ))}

                            {suggestions.length > 0 && (
                                <li className="border-t">
                                    <button
                                        onClick={handleSearchSubmit}
                                        className="w-full text-center px-4 py-2 text-sm text-orange-600 hover:bg-gray-100 font-medium"
                                    >
                                        Все результаты поиска
                                    </button>
                                </li>
                            )}
                        </ul>
                    )}
                    {!isLoading && suggestions.length === 0 && debouncedQuery.length < 2 && query.length > 0 && (
                        <div className="p-4 text-center text-gray-500 text-sm">
                            Введите еще символы для поиска...
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default Searchbar;

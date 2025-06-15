import React, {useState, useEffect, useCallback} from 'react';
import {Link} from 'react-router-dom';
import {fetchPromotions} from '../services/api';
import PromotionCard from '../components/promotions/PromotionCard';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorMessage from '../components/ui/ErrorMessage';
import Button from '../components/ui/Button';

const PromotionsPage = () => {
    const [promotionsData, setPromotionsData] = useState({count: 0, next: null, previous: null, results: []});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);


    const loadPromotions = useCallback(async (url = null) => {
        setLoading(true);
        setError(null);
        try {
            const data = await fetchPromotions(url);
            setPromotionsData(data);
        } catch (err) {
            setError(err.message || 'Не удалось загрузить список акций.');
            console.error("Promotions page fetch error:", err);
            setPromotionsData({count: 0, next: null, previous: null, results: []});
        } finally {
            setLoading(false);
        }
    }, []);


    useEffect(() => {
        loadPromotions();
    }, [loadPromotions]);


    const handleNextPage = () => {
        if (promotionsData.next) loadPromotions(promotionsData.next);
    };
    const handlePreviousPage = () => {
        if (promotionsData.previous) loadPromotions(promotionsData.previous);
    };

    return (
        <div className="container mx-auto px-4 py-8 md:py-12">

            <nav className="text-sm mb-6 text-gray-500">
                <Link to="/" className="hover:text-orange-500">Главная</Link>
                <span className="mx-2">/</span>
                <span>Акции</span>
            </nav>

            <h1 className="text-3xl md:text-4xl font-bold mb-8 text-gray-800">
                Все акции и спецпредложения
            </h1>

            {loading && <LoadingSpinner text="Загрузка акций..." className="my-16"/>}
            {error && <ErrorMessage message={error} onRetry={() => loadPromotions()} className="my-16"/>}

            {!loading && !error && promotionsData.results.length > 0 && (
                <>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
                        {promotionsData.results.map((promo) => (
                            <PromotionCard key={promo.id} promotion={promo}/>
                        ))}
                    </div>


                    {(promotionsData.next || promotionsData.previous) && (
                        <div className="mt-8 flex justify-center items-center gap-4">
                            <Button onClick={handlePreviousPage} disabled={!promotionsData.previous || loading}
                                    variant="outline">Назад</Button>
                            <Button onClick={handleNextPage} disabled={!promotionsData.next || loading}
                                    variant="outline">Вперед</Button>
                        </div>
                    )}
                    <div className="mt-4 text-center text-sm text-gray-500">
                        Всего акций: {promotionsData.count}
                    </div>
                </>
            )}


            {!loading && !error && promotionsData.results.length === 0 && (
                <div className="text-center py-10 text-gray-500 border bg-white rounded-lg shadow-sm">
                    <p className="text-lg mb-4">Действующих акций пока нет.</p>
                    <p>Следите за обновлениями!</p>
                </div>
            )}
        </div>
    );
};

export default PromotionsPage;

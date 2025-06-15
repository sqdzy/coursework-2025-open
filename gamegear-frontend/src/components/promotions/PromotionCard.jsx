import React from 'react';
import {Link} from 'react-router-dom';
import {Tag, Calendar, ArrowRight} from 'lucide-react';
import Button from '../ui/Button';


const formatDate = (dateString) => {
    if (!dateString) return '';
    try {
        return new Intl.DateTimeFormat('ru-RU', {
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        }).format(new Date(dateString));
    } catch {
        return dateString;
    }
};


const formatDiscount = (type, value) => {
    const numValue = parseFloat(value);
    if (isNaN(numValue)) return '-';

    switch (type) {
        case 'percentage':
            return `-${numValue.toFixed(0)}%`;
        case 'fixed':
            return `-${new Intl.NumberFormat('ru-RU').format(numValue)} ₽`;
        case 'special_price':
            return `Цена: ${new Intl.NumberFormat('ru-RU', {
                style: 'currency',
                currency: 'RUB',
                minimumFractionDigits: 0
            }).format(numValue)}`;
        default:
            return `${value}`;
    }
};

const PromotionCard = ({promotion}) => {
    if (!promotion) return null;

    const {id, name, description, discount_type, discount_value, start_date, end_date} = promotion;
    const promotionProductsLink = `/catalog?promotion_id=${id}`;

    return (
        <div
            className="bg-white border rounded-lg shadow-sm overflow-hidden flex flex-col h-full transition-shadow hover:shadow-md">

            <div className="p-4 flex-grow flex flex-col">
                <h3 className="text-lg font-semibold text-gray-800 mb-2">{name}</h3>
                <p className="text-sm text-gray-600 mb-3 flex-grow">
                    {description && description.length > 100 ? `${description.substring(0, 97)}...` : description}
                </p>


                <div className="space-y-2 text-sm mb-4">
                    <div className="flex items-center gap-2 text-orange-600 font-medium">
                        <Tag size={16}/>
                        <span>{formatDiscount(discount_type, discount_value)}</span>
                    </div>
                    <div className="flex items-center gap-2 text-gray-500">
                        <Calendar size={16}/>
                        <span>до {formatDate(end_date)}</span>
                    </div>
                </div>


                <div className="mt-auto pt-4 border-t">
                    <Link to={promotionProductsLink}>
                        <Button variant="outline" size="sm"
                                className="w-full sm:w-auto">
                            К товарам акции ->
                        </Button>
                    </Link>
                </div>

            </div>

        </div>
    );
};

export default PromotionCard;

import React from 'react';
import {Link} from 'react-router-dom';

import {
    MousePointer2,
    Keyboard,
    Headphones,
    Square,
    Monitor,
    Gamepad2,
    Camera,
    Mic2,
    Speaker,
    Armchair,
    Table,
    Cable,
    HelpCircle
} from 'lucide-react';


const categoryIcons = {
    'Мыши': MousePointer2,
    'Клавиатуры': Keyboard,
    'Гарнитуры': Headphones,
    'Коврики для мыши': Square,
    'Мониторы': Monitor,
    'Геймпады': Gamepad2,
    'Веб-камеры': Camera,
    'Микрофоны': Mic2,
    'Акустика': Speaker,
    'Игровые кресла': Armchair,
    'Столы': Table,
    'Аксессуары (кабели, подставки, держатели)': Cable,

};

const CategoryList = ({categories}) => {
    if (!categories || categories.length === 0) {
        return null;
    }

    return (
        <section className="mb-8 md:mb-12">
            <h2 className="text-xl md:text-2xl font-semibold mb-4">Категории товаров</h2>
            <div
                className="flex space-x-4 overflow-x-auto pb-4 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100 md:grid md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 md:gap-4 md:space-x-0 md:overflow-x-visible">
                {categories.map((category) => {

                    const IconComponent = categoryIcons[category.name] || HelpCircle;

                    return (
                        <Link
                            to={`/categories/${category.id}`}
                            key={category.id}
                            className="flex-shrink-0 w-36 md:w-auto bg-white border rounded-lg p-4 text-center shadow hover:shadow-md hover:border-orange-300 transition-all duration-200 group flex flex-col items-center justify-center"
                        >

                            <div
                                className="h-12 w-12 mb-3 bg-orange-100 rounded-full flex items-center justify-center text-orange-500 group-hover:bg-orange-500 group-hover:text-white transition-colors duration-200">
                                <IconComponent size={28} strokeWidth={1.5}/>
                            </div>
                            <span
                                className="text-sm font-medium text-gray-700 group-hover:text-orange-600 leading-tight"> 
                                {category.name}
                            </span>
                        </Link>
                    );
                })}
            </div>
        </section>
    );
};

export default CategoryList;

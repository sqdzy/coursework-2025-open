import React from 'react';

const Footer = () => {
  return (
    <footer className="bg-gray-800 text-white py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <h3 className="font-bold text-lg mb-4">GAMEGEAR</h3>
            <p className="text-gray-300 text-sm">
              Магазин игровой периферии. Наушники, мыши, клавиатуры и другие аксессуары для геймеров.
            </p>
          </div>

          <div>
            <h4 className="font-bold mb-4">Компания</h4>
            <ul className="space-y-2">
              <li><a href="#" className="text-gray-300 hover:text-white">О нас</a></li>
              <li><a href="#" className="text-gray-300 hover:text-white">Контакты</a></li>
              <li><a href="#" className="text-gray-300 hover:text-white">Вакансии</a></li>
              <li><a href="#" className="text-gray-300 hover:text-white">Новости</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold mb-4">Информация</h4>
            <ul className="space-y-2">
              <li><a href="#" className="text-gray-300 hover:text-white">Доставка</a></li>
              <li><a href="#" className="text-gray-300 hover:text-white">Оплата</a></li>
              <li><a href="#" className="text-gray-300 hover:text-white">Гарантия</a></li>
              <li><a href="#" className="text-gray-300 hover:text-white">Возврат</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold mb-4">Контакты</h4>
            <p className="text-gray-300 mb-2">+7 (951) 075 65 20</p>
            <p className="text-gray-300 mb-2">info@gamegear.ru</p>
            <p className="text-gray-300">г. Москва, ул. Прянишникова 2А</p>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-gray-700 text-center text-gray-400 text-sm">
          <p>© 2025 GAMEGEAR. Все права защищены.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
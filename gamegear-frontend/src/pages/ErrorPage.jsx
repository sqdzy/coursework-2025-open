import React from 'react';
import Layout from '../components/layout/Layout';
import Button from '../components/ui/Button';
import { RefreshCw } from 'lucide-react';

const ErrorPage = ({ message, onRetry }) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="text-center max-w-md">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Ошибка загрузки</h2>
        <p className="text-gray-600 mb-8">{message || 'Не удалось загрузить данные о товаре. Пожалуйста, попробуйте позже.'}</p>
        <Button
          onClick={onRetry || (() => window.location.reload())}
          className="inline-flex items-center"
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Попробовать снова
        </Button>
      </div>
    </div>
  );
};

export default ErrorPage;
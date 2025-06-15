import React from 'react';
import Button from './Button';

const ErrorMessage = ({message, onRetry, className = ""}) => {
    return (
        <div className={`p-4 text-center bg-red-50 border border-red-200 rounded-md ${className}`}>
            <p className="text-sm font-medium text-red-700">{message || 'Произошла ошибка.'}</p>
            {onRetry && (
                <Button onClick={onRetry} variant="secondary" size="sm" className="mt-3">
                    Попробовать снова
                </Button>
            )}
        </div>
    );
};

export default ErrorMessage;

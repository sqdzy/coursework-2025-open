
import React, { useEffect } from 'react';
import { X as CloseIcon } from 'lucide-react';

const Modal = ({ isOpen, onClose, title, children, size = 'md', footerContent = null }) => {
    useEffect(() => {
        const handleEscape = (event) => {
            if (event.key === 'Escape') { onClose(); }
        };
        if (isOpen) { document.addEventListener('keydown', handleEscape); }
        return () => { document.removeEventListener('keydown', handleEscape); };
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    const sizeClasses = {
        sm: 'max-w-sm', md: 'max-w-md', lg: 'max-w-lg', xl: 'max-w-xl',
        '2xl': 'max-w-2xl', '3xl': 'max-w-3xl', '4xl': 'max-w-4xl', '5xl': 'max-w-5xl' 
    };
    const modalWidthClass = sizeClasses[size] || sizeClasses.md;

    return (
        <div
            className="fixed inset-0 bg-black bg-opacity-75 z-[100] flex justify-center items-center p-4 transition-opacity duration-300 ease-out" 
            onClick={onClose}
            role="dialog"
            aria-modal="true"
            aria-labelledby="modal-title"
        >
            <div
                className={`bg-white rounded-lg shadow-xl w-full ${modalWidthClass} flex flex-col max-h-[90vh] overflow-hidden transform scale-95 opacity-0 animate-modal-enter`} 
                onClick={(e) => e.stopPropagation()}
                role="document"
            >
                <div className="flex justify-between items-center p-4 border-b flex-shrink-0">
                    <h2 id="modal-title" className="text-lg font-semibold text-gray-800 truncate pr-2">
                        {title}
                    </h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1 rounded-full hover:bg-gray-100" aria-label="Закрыть">
                        <CloseIcon size={22} />
                    </button>
                </div>

                <div className="p-4 sm:p-6 overflow-y-auto flex-grow">
                    {children}
                </div>

                {footerContent && (
                     <div className="flex justify-end items-center p-4 border-t bg-gray-50 rounded-b-lg flex-shrink-0">
                         {footerContent}
                     </div>
                )}
            </div>
            <style jsx global>{`
                @keyframes modal-enter { from { transform: scale(0.95) translateY(10px); opacity: 0; } to { transform: scale(1) translateY(0); opacity: 1; } }
                .animate-modal-enter { animation: modal-enter 0.2s ease-out forwards; }
            `}</style>
        </div>
    );
};

export default Modal;

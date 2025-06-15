import React, {useState, useEffect} from 'react';
import {useAuth} from '../context/AuthContext';
import {updateUserDetails} from '../../services/api';
import Button from '../ui/Button';
import ErrorMessage from '../ui/ErrorMessage';

const EditProfileForm = ({initialData, onSuccess, onCancel}) => {
    const {token, user: currentUser, login} = useAuth();
    const [formData, setFormData] = useState({
        email: initialData?.email || '',
        first_name: initialData?.first_name || '',
        last_name: initialData?.last_name || '',
    });
    const [loading, setLoading] = useState(false);
    const [errors, setErrors] = useState({});


    useEffect(() => {
        setFormData({
            email: initialData?.email || '',
            first_name: initialData?.first_name || '',
            last_name: initialData?.last_name || '',
        });
        setErrors({});
    }, [initialData]);

    const handleChange = (e) => {
        const {name, value} = e.target;
        setFormData(prev => ({...prev, [name]: value}));

        if (errors[name]) {
            setErrors(prev => ({...prev, [name]: undefined}));
        }
        if (errors.detail) {
            setErrors(prev => ({...prev, detail: undefined}));
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setErrors({});

        try {

            const updatedData = await updateUserDetails(formData, token);
            console.log("Profile updated successfully:", updatedData);


            const updatedLocalStorageUser = {...currentUser, ...updatedData};
            localStorage.setItem('authUser', JSON.stringify(updatedLocalStorageUser));


            onSuccess(updatedData);
        } catch (error) {
            console.error("Profile update error:", error);
            if (error.validationErrors) {

                setErrors(error.validationErrors);
            } else {

                setErrors({detail: error.message || 'Не удалось обновить профиль.'});
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            {errors.detail && <ErrorMessage message={errors.detail}/>}

            <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
                <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className={`mt-1 block w-full px-3 py-2 border ${errors.email ? 'border-red-500' : 'border-gray-300'} rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm disabled:bg-gray-100`}
                    disabled={loading}
                />
                {errors.email &&
                    <p className="mt-1 text-xs text-red-600">{errors.email.join ? errors.email.join(', ') : errors.email}</p>}
            </div>

            <div>
                <label htmlFor="first_name" className="block text-sm font-medium text-gray-700">Имя</label>
                <input
                    type="text"
                    id="first_name"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleChange}
                    className={`mt-1 block w-full px-3 py-2 border ${errors.first_name ? 'border-red-500' : 'border-gray-300'} rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm disabled:bg-gray-100`}
                    disabled={loading}
                />
                {errors.first_name &&
                    <p className="mt-1 text-xs text-red-600">{errors.first_name.join ? errors.first_name.join(', ') : errors.first_name}</p>}
            </div>

            <div>
                <label htmlFor="last_name" className="block text-sm font-medium text-gray-700">Фамилия</label>
                <input
                    type="text"
                    id="last_name"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleChange}
                    className={`mt-1 block w-full px-3 py-2 border ${errors.last_name ? 'border-red-500' : 'border-gray-300'} rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm disabled:bg-gray-100`}
                    disabled={loading}
                />
                {errors.last_name &&
                    <p className="mt-1 text-xs text-red-600">{errors.last_name.join ? errors.last_name.join(', ') : errors.last_name}</p>}
            </div>


            <div className="flex justify-end gap-3 pt-4 border-t">
                <Button type="button" onClick={onCancel} variant="outline" disabled={loading}>
                    Отмена
                </Button>
                <Button type="submit" variant="primary" disabled={loading}>
                    {loading ? 'Сохранение...' : 'Сохранить изменения'}
                </Button>
            </div>
        </form>
    );
};

export default EditProfileForm;

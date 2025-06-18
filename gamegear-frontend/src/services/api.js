const API_BASE_URL = 'https://api-gg.familycore.ru/api';


async function handleApiResponse(response, operation = 'fetching data') {
    if (!response.ok) {
        let errorBody = {detail: `API error ${response.status} during ${operation}.`};
        try {
            errorBody = await response.json();
        } catch (e) {
        }
        console.error(`API Response Error (${response.status}) during ${operation}:`, errorBody);
        throw new Error(errorBody.detail || JSON.stringify(errorBody));
    }
    if (response.status === 204) {
        return null;
    }
    return await response.json();
}

export const fetchProduct = async (productId) => {
    if (!productId) throw new Error("Product ID is required.");
    try {
        const response = await fetch(`${API_BASE_URL}/products/${productId}/`);

        return await handleApiResponse(response, 'fetching product');
    } catch (error) {
        console.error('Error in fetchProduct:', error);
        throw error;
    }
};


export const fetchProducts = async () => {
    try {

        const response = await fetch(`${API_BASE_URL}/products/`);

        if (!response.ok) {
            let errorBody = null;
            try {
                errorBody = await response.json();
            } catch (e) {
            }

            console.error('API Response Error:', response.status, errorBody);
            throw new Error(`API error: ${response.status} - ${response.statusText}. ${errorBody ? JSON.stringify(errorBody) : ''}`);
        }

        const data = await response.json();


        return data.results;
    } catch (error) {
        console.error('Error fetching products:', error);
        throw error;
    }
};


export const fetchCategories = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/categories/`);
        if (!response.ok) throw new Error(`API error: ${response.status}`);
        const data = await response.json();
        return data.results;
    } catch (error) {
        console.error('Error fetching categories:', error);
        throw error;
    }
}


/**
 * Получает список одобренных отзывов для товара.
 * @param {number | string} productId ID товара
 * @returns {Promise<Array>} Массив объектов отзывов
 */
export const fetchReviews = async (productId, url = null) => {
  if (!productId && !url) throw new Error("Product ID or URL is required for fetching reviews.");
  const requestUrl = url || `${API_BASE_URL}/reviews/?product_id=${productId}`;
  try {
    const response = await fetch(requestUrl);
    const data = await handleApiResponse(response, `fetching reviews for product ${productId || 'given URL'}`);
    return data;
  } catch (error) { console.error(`Error in fetchReviews:`, error); throw error; }
};

export const createReview = async (productId, rating, text, images = [], authToken) => {
    if (!authToken) throw new Error("Authentication required.");
    if (!productId || !rating || !text) throw new Error("Product ID, rating, and text are required.");
    const formData = new FormData();
    formData.append('product', productId);
    formData.append('rating', rating);
    formData.append('text', text);
    if (images && images.length > 0) {
        images.forEach((imageFile) => { formData.append('uploaded_images', imageFile, imageFile.name); });
    }
    try {
        const response = await fetch(`${API_BASE_URL}/reviews/`, {
            method: 'POST',
            headers: { 'Authorization': `Token ${authToken}` },
            body: formData,
        });
        return await handleApiResponse(response, 'creating review');
    } catch (error) { console.error('Error in createReview:', error); throw error; }
};

export const updateReview = async (reviewId, dataToUpdate, authToken) => {
    if (!authToken) throw new Error("Authentication required.");
    if (!reviewId) throw new Error("Review ID is required.");
    const formData = new FormData();
    if (dataToUpdate.rating !== undefined) formData.append('rating', dataToUpdate.rating);
    if (dataToUpdate.text !== undefined) formData.append('text', dataToUpdate.text);
    if (dataToUpdate.imagesToAdd && dataToUpdate.imagesToAdd.length > 0) {
        dataToUpdate.imagesToAdd.forEach(file => { formData.append('uploaded_images', file, file.name); });
    }
    if (dataToUpdate.imagesToDeleteIds && dataToUpdate.imagesToDeleteIds.length > 0) {
        dataToUpdate.imagesToDeleteIds.forEach(id => { formData.append('delete_images_ids', id); });
    }
    try {
        const response = await fetch(`${API_BASE_URL}/reviews/${reviewId}/`, {
            method: 'PATCH',
            headers: { 'Authorization': `Token ${authToken}` },
            body: formData,
        });
        return await handleApiResponse(response, 'updating review');
    } catch (error) { console.error('Error in updateReview:', error); throw error; }
};

export const deleteReview = async (reviewId, authToken) => {
  if (!authToken) throw new Error("Authentication required.");
  if (!reviewId) throw new Error("Review ID is required.");
  try {
    const response = await fetch(`${API_BASE_URL}/reviews/${reviewId}/`, {
      method: 'DELETE',
      headers: { 'Authorization': `Token ${authToken}` },
    });
    return await handleApiResponse(response, 'deleting review');
  } catch (error) { console.error('Error in deleteReview:', error); throw error; }
};

export const fetchHomepageData = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/homepage/`);

        return await handleApiResponse(response, 'fetching homepage data');
    } catch (error) {
        console.error('Error in fetchHomepageData:', error);
        throw error;
    }
};

export const fetchCategoryDetail = async (categoryId) => {
    if (!categoryId) throw new Error("Category ID is required.");
    try {

        const response = await fetch(`${API_BASE_URL}/categories/${categoryId}/`);

        return await handleApiResponse(response, `fetching category detail for ID ${categoryId}`);
    } catch (error) {
        console.error(`Error in fetchCategoryDetail for ID ${categoryId}:`, error);
        throw error;
    }
};

export const loginOrRegisterUser = async (username, password) => {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login-or-register/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',

            },
            body: JSON.stringify({username, password}),
        });

        return await handleApiResponse(response, 'login or register');
    } catch (error) {

        throw error;
    }
};

export const fetchCartItems = async (authToken) => {
    if (!authToken) throw new Error("Authentication required to fetch cart.");
    try {
        const response = await fetch(`${API_BASE_URL}/cart/`, {
            headers: {
                'Authorization': `Token ${authToken}`,
            },
        });
        return await handleApiResponse(response, 'fetching cart items');
    } catch (error) {
        console.error('Error fetching cart items:', error);
        throw error;
    }
};

export const addCartItem = async (productId, quantity = 1, authToken) => {
    if (!authToken) throw new Error("Authentication required to add to cart.");
    if (!productId) throw new Error("Product ID is required.");
    try {
        const response = await fetch(`${API_BASE_URL}/cart/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Token ${authToken}`,
            },
            body: JSON.stringify({
                product_id: productId,
                quantity: quantity
            }),
        });

        return await handleApiResponse(response, 'adding cart item');
    } catch (error) {
        console.error('Error adding cart item:', error);
        throw error;
    }
};

export const updateCartItem = async (cartItemId, quantity, authToken) => {
    if (!authToken) throw new Error("Authentication required to update cart.");
    if (!cartItemId) throw new Error("Cart Item ID is required.");
    if (quantity < 1) throw new Error("Quantity must be at least 1.");
    try {
        const response = await fetch(`${API_BASE_URL}/cart/${cartItemId}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Token ${authToken}`,
            },
            body: JSON.stringify({quantity: quantity}),
        });
        return await handleApiResponse(response, 'updating cart item quantity');
    } catch (error) {
        console.error('Error updating cart item:', error);
        throw error;
    }
};

export const deleteCartItem = async (cartItemId, authToken) => {
    if (!authToken) throw new Error("Authentication required to delete from cart.");
    if (!cartItemId) throw new Error("Cart Item ID is required.");
    try {
        const response = await fetch(`${API_BASE_URL}/cart/${cartItemId}/`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Token ${authToken}`,
            },
        });

        return await handleApiResponse(response, 'deleting cart item');
    } catch (error) {
        console.error('Error deleting cart item:', error);
        throw error;
    }
};

export const fetchSearchSuggestions = async (query) => {
    if (!query || query.trim().length < 1) {
        return [];
    }
    try {

        const encodedQuery = encodeURIComponent(query);

        const response = await fetch(`${API_BASE_URL}/products/search-suggestions/?search=${encodedQuery}`);
        const data = await handleApiResponse(response, `fetching search suggestions for "${query}"`);

        return Array.isArray(data) ? data : [];
    } catch (error) {
        console.error(`Error fetching search suggestions for "${query}":`, error);

        return [];
    }
};


export const fetchCatalogProducts = async (url = null, searchQuery = null) => {
    let requestUrl;

    if (url) {

        requestUrl = url;
    } else {

        requestUrl = `${API_BASE_URL}/products/`;
        if (searchQuery && searchQuery.trim()) {
            requestUrl += `?search=${encodeURIComponent(searchQuery.trim())}`;
        }


    }

    console.log("fetchCatalogProducts requesting:", requestUrl);

    try {
        const response = await fetch(requestUrl);

        const data = await handleApiResponse(response, `fetching catalog/search products`);

        if (typeof data === 'object' && data !== null && 'results' in data) {
            return data;
        } else {
            console.warn("fetchCatalogProducts received unexpected data format:", data);

            return {count: 0, next: null, previous: null, results: []};
        }
    } catch (error) {
        console.error('Error in fetchCatalogProducts:', error);
        throw error;
    }
};

export const fetchDeliveryMethods = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/delivery-methods/`);
        const data = await handleApiResponse(response, 'fetching delivery methods');

        return Array.isArray(data) ? data : (data?.results || []);
    } catch (error) {
        console.error('Error fetching delivery methods:', error);
        throw error;
    }
};

export const fetchPaymentMethods = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/payment-methods/`);
        const data = await handleApiResponse(response, 'fetching payment methods');
        return Array.isArray(data) ? data : (data?.results || []);
    } catch (error) {
        console.error('Error fetching payment methods:', error);
        throw error;
    }
};

export const createOrder = async (orderDetails, authToken) => {

    if (!authToken) throw new Error("Authentication required to create order.");
    if (!orderDetails) throw new Error("Order details are required.");

    try {
        const response = await fetch(`${API_BASE_URL}/orders/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Token ${authToken}`,
            },
            body: JSON.stringify(orderDetails),
        });

        return await handleApiResponse(response, 'creating order');
    } catch (error) {
        console.error('Error creating order:', error);
        throw error;
    }
};

export const fetchUserDetails = async (authToken) => {
    if (!authToken) throw new Error("Authentication required to fetch user details.");
    try {

        const response = await fetch(`${API_BASE_URL}/auth/user/`, {
            headers: {
                'Authorization': `Token ${authToken}`,
            },
        });
        return await handleApiResponse(response, 'fetching user details');
    } catch (error) {
        console.error('Error fetching user details:', error);
        throw error;
    }
};

export const fetchUserOrders = async (authToken, url = null) => {

    if (!authToken) throw new Error("Authentication required to fetch orders.");
    try {
        const requestUrl = url || `${API_BASE_URL}/orders/`;
        const response = await fetch(requestUrl, {
            headers: {
                'Authorization': `Token ${authToken}`,
            },
        });
        const data = await handleApiResponse(response, 'fetching user orders');

        if (typeof data === 'object' && data !== null && 'results' in data) {
            return data;
        } else {
            console.warn("fetchUserOrders received unexpected data format:", data);
            return {count: 0, next: null, previous: null, results: Array.isArray(data) ? data : []};
        }
    } catch (error) {
        console.error('Error fetching user orders:', error);
        throw error;
    }
};

export const updateUserDetails = async (userData, authToken) => {

    if (!authToken) throw new Error("Authentication required to update profile.");
    if (!userData) throw new Error("User data is required.");

    try {

        const response = await fetch(`${API_BASE_URL}/auth/user/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Token ${authToken}`,
            },
            body: JSON.stringify(userData),
        });

        return await handleApiResponse(response, 'updating user details');
    } catch (error) {
        console.error('Error updating user details:', error);

        if (error.message.includes('400')) {
            try {

                const errorBody = JSON.parse(error.message.substring(error.message.indexOf('{')));
                throw {validationErrors: errorBody};
            } catch (parseError) {

                throw new Error(error.message || 'Ошибка валидации данных профиля.');
            }
        }
        throw error;
    }
};

export const fetchPromotions = async (url = null) => {
    const requestUrl = url || `${API_BASE_URL}/promotions/`;
    console.log("fetchPromotions requesting:", requestUrl);

    try {
        const response = await fetch(requestUrl);

        const data = await handleApiResponse(response, 'fetching promotions');
        if (typeof data === 'object' && data !== null && 'results' in data) {
            return data;
        } else {
            console.warn("fetchPromotions received unexpected data format:", data);
            return {count: 0, next: null, previous: null, results: []};
        }
    } catch (error) {
        console.error('Error fetching promotions:', error);
        throw error;
    }
};

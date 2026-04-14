// Глобальные переменные состояния
let userWallets =[];
let socket = null;
let productsMap = {}; // Кэш товаров для быстрого доступа при покупке

// ==========================================
// ИНИЦИАЛИЗАЦИЯ
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    // Ждем загрузки данных текущего пользователя (из main.js)
    if (window.currentUser) {
        initIbay();
    } else {
        document.addEventListener('UserDataLoaded', initIbay);
    }
});

async function initIbay() {
    await fetchWallets();
    fetchProducts();
    initWebSockets();

    // Навигация по вкладкам
    document.getElementById('btnShowProducts').addEventListener('click', (e) => switchTab('products', e.target));
    document.getElementById('btnShowOrders').addEventListener('click', (e) => {
        switchTab('orders', e.target);
        fetchOrders();
    });

    // Открытие модалки создания товара
    document.getElementById('btnOpenCreateModal').addEventListener('click', () => {
        populateWalletSelect('prodWalletSelect');
        document.getElementById('modalCreateProduct').classList.remove('hidden');
    });

    // Обработчик создания товара
    document.getElementById('formCreateProduct').addEventListener('submit', handleCreateProduct);

    // Обработчик покупки товара
    document.getElementById('formBuyProduct').addEventListener('submit', handleBuyProduct);
}

// ==========================================
// ОБРАБОТЧИКИ ФОРМ (БИЗНЕС-ЛОГИКА)
// ==========================================

async function handleCreateProduct(e) {
    e.preventDefault();
    const btnSubmit = e.target.querySelector('button[type="submit"]');
    btnSubmit.disabled = true; // Защита от двойного клика

    const data = {
        title: document.getElementById('prodTitle').value,
        price_eth: parseFloat(document.getElementById('prodPrice').value),
        wallet_id: document.getElementById('prodWalletSelect').value,
        photo_url: document.getElementById('prodPhotoUrl').value || null
    };

    try {
        const res = await fetch('/api/v1/ibay/products', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (res.ok) {
            showNotification('Товар успешно опубликован!', false);
            closeModal('modalCreateProduct');
            e.target.reset();
            // Список обновится автоматически по событию WebSockets
        } else {
            const err = await res.json();
            showNotification(err.detail || 'Ошибка при создании товара', true);
        }
    } catch (error) {
        console.error('Create Product Error:', error);
        showNotification('Произошла сетевая ошибка', true);
    } finally {
        btnSubmit.disabled = false;
    }
}

async function handleBuyProduct(e) {
    e.preventDefault();
    const btnSubmit = e.target.querySelector('button[type="submit"]');
    btnSubmit.disabled = true; // Блокируем кнопку на время транзакции

    const productId = document.getElementById('buyProductId').value;
    const buyerWalletId = document.getElementById('buyWalletSelect').value;
    const priceEth = parseFloat(document.getElementById('buyPrice').dataset.price);

    const product = productsMap[productId];

    if (!product || !product.seller_address) {
        showNotification('Ошибка данных товара. Попробуйте обновить страницу.', true);
        btnSubmit.disabled = false;
        return;
    }

    const sellerAddress = product.seller_address; // НАСТОЯЩИЙ АДРЕС ПРОДАВЦА ИЗ API

    if (!buyerWalletId) {
        showNotification('Пожалуйста, выберите кошелек для оплаты', true);
        btnSubmit.disabled = false;
        return;
    }

    try {
        showNotification('Инициация транзакции в блокчейне...', false);

        // ШАГ 1: Отправляем транзакцию через микросервис Ethereum
        const txRes = await fetch('/api/v1/transactions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                wallet_id: buyerWalletId,
                to_address: sellerAddress, // ИСПОЛЬЗУЕМ РЕАЛЬНЫЙ КОШЕЛЕК
                value: priceEth
            })
        });

        if (!txRes.ok) {
            const err = await txRes.json();
            throw new Error(err.detail || 'Ошибка при отправке транзакции');
        }

        const txData = await txRes.json();
        const realTxHash = txData.tx_hash; // Получаем НАСТОЯЩИЙ хэш транзакции

        // ШАГ 2: Создаем заказ в iBay с реальным хэшем
        showNotification('Транзакция отправлена! Формируем заказ...', false);

        const orderRes = await fetch('/api/v1/ibay/orders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_id: productId,
                price_eth: priceEth,
                tx_hash: realTxHash
            })
        });

        if (orderRes.ok) {
            showNotification('Заказ успешно создан! Ожидаем подтверждения сети.', false);
            closeModal('modalBuyProduct');
            document.getElementById('btnShowOrders').click(); // Переключаем на вкладку заказов
        } else {
            const err = await orderRes.json();
            throw new Error(err.detail || 'Транзакция ушла, но заказ не создан');
        }

    } catch (error) {
        console.error('Buy Product Error:', error);
        showNotification(error.message, true);
    } finally {
        btnSubmit.disabled = false;
    }
}

// ==========================================
// ЛОГИКА WEBSOCKETS
// ==========================================
function initWebSockets() {
    const token = getCookie('access_token');
    if (!token) return;

    socket = io('/ibay', {
        auth: { token: token }
    });

    socket.on('connect', () => {
        console.log('iBay WebSocket подключен!');
    });

    // Обработка появления нового товара на площадке
    socket.on('ibay_product_created', (data) => {
        console.log('Новый товар в сети:', data);
        if (!document.getElementById('productsView').classList.contains('hidden')) {
            fetchProducts();
        }
    });

    // Обработка создания и изменения статусов заказов
    socket.on('ibay_order_created', handleOrderEvent);
    socket.on('ibay_order_updated', handleOrderEvent);

    function handleOrderEvent(data) {
        console.log('Событие заказа:', data);
        // Проверяем, что заказ касается текущего пользователя
        if (window.currentUser && data.buyer_id === window.currentUser.id) {
            // Если открыта вкладка заказов - обновляем список
            if (!document.getElementById('ordersView').classList.contains('hidden')) {
                fetchOrders();
            }

            // Показываем уведомление о смене статуса
            if (data.status) {
                const isError = data.status === 'FAILED' || data.status === 'RETURNED';
                showNotification(`Заказ обновлен. Новый статус: ${data.status}`, isError);
            }
        }
    }
}

// ==========================================
// ФУНКЦИИ API И РЕНДЕРА
// ==========================================

async function fetchProducts() {
    try {
        const res = await fetch('/api/v1/ibay/products');
        const products = await res.json();

        const container = document.getElementById('productsView');
        container.innerHTML = '';
        productsMap = {}; // Очищаем кэш

        if (products.length === 0) {
            container.innerHTML = '<p>Товаров пока нет.</p>';
            return;
        }

        products.forEach(p => {
            productsMap[p.id] = p; // Сохраняем товар с seller_address в кэш

            const imgUrl = p.photo_url || '/static/img/default-product.png';
            // ЗАЩИТА ОТ XSS: экранируем заголовок товара
            const safeTitle = escapeHTML(p.title);

            const card = document.createElement('div');
            card.className = 'product-card';
            card.innerHTML = `
                <img src="${escapeHTML(imgUrl)}" alt="Product" class="product-img" onerror="this.src='/static/img/default-product.png'">
                <div class="product-title">${safeTitle}</div>
                <div class="product-price">${p.price_eth} ETH</div>
                <button class="btn btn-primary mt-auto" onclick="openBuyModal('${p.id}')">Купить</button>
            `;
            container.appendChild(card);
        });
    } catch (error) {
        console.error('Error fetching products:', error);
    }
}

async function fetchOrders() {
    try {
        const res = await fetch('/api/v1/ibay/orders');
        const orders = await res.json();
        const container = document.getElementById('ordersView');
        container.innerHTML = '';

        if (orders.length === 0) {
            container.innerHTML = '<p>Вы еще ничего не заказывали.</p>';
            return;
        }

        orders.forEach(o => {
            // Экранирование данных
            const safeId = escapeHTML(o.id.substring(0,8));
            const safeTx = escapeHTML(o.tx_hash.substring(0, 14));
            const safeStatus = escapeHTML(o.status);

            const card = document.createElement('div');
            card.className = 'order-card';
            card.innerHTML = `
                <div>
                    <strong>Order ID:</strong> ${safeId}...<br>
                    <small>Цена: ${o.price_eth} ETH | Tx: <a href="https://sepolia.etherscan.io/tx/${o.tx_hash}" target="_blank">${safeTx}...</a></small>
                </div>
                <span class="order-status status-${safeStatus.toLowerCase()}">${safeStatus}</span>
            `;
            container.appendChild(card);
        });
    } catch (error) {
        console.error('Error fetching orders:', error);
    }
}

async function fetchWallets() {
    try {
        const res = await fetch('/api/v1/wallets');
        if (res.ok) {
            userWallets = await res.json();
        }
    } catch (error) {
        console.error('Error fetching wallets:', error);
    }
}

function populateWalletSelect(selectId) {
    const select = document.getElementById(selectId);
    select.innerHTML = '<option value="" disabled selected>Выберите кошелек...</option>';
    userWallets.forEach(w => {
        const option = document.createElement('option');
        option.value = w.id;
        option.textContent = `${w.address.substring(0,6)}...${w.address.slice(-4)} (${w.balance} ETH)`;
        select.appendChild(option);
    });
}

// ==========================================
// UI УТИЛИТЫ И ХЕЛПЕРЫ
// ==========================================

function switchTab(tab, btnElement) {
    document.getElementById('productsView').classList.add('hidden');
    document.getElementById('ordersView').classList.add('hidden');
    document.getElementById(tab + 'View').classList.remove('hidden');

    document.getElementById('btnShowProducts').classList.remove('active');
    document.getElementById('btnShowOrders').classList.remove('active');
    btnElement.classList.add('active');
}

function openBuyModal(productId) {
    const product = productsMap[productId];
    if (!product) return;

    document.getElementById('buyProductId').value = product.id;
    document.getElementById('buyTitle').innerText = product.title;

    const priceEl = document.getElementById('buyPrice');
    priceEl.innerText = product.price_eth + " ETH";
    priceEl.dataset.price = product.price_eth; // Сохраняем чистую цифру в data-атрибут

    populateWalletSelect('buyWalletSelect');
    document.getElementById('modalBuyProduct').classList.remove('hidden');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

// Вспомогательная функция для защиты от XSS атак
function escapeHTML(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Система Toast-уведомлений
function showNotification(message, isError = false) {
    const toast = document.createElement('div');
    toast.textContent = message;

    // Стилизуем всплывающее окно
    Object.assign(toast.style, {
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        padding: '15px 25px',
        background: isError ? '#e74c3c' : '#2ecc71',
        color: 'white',
        borderRadius: '5px',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        zIndex: '9999',
        transition: 'opacity 0.3s ease-in-out',
        fontWeight: 'bold',
        fontSize: '14px'
    });

    document.body.appendChild(toast);

    // Удаляем через 4 секунды
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Парсинг Cookie для JWT токена
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

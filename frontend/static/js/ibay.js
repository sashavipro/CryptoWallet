// Глобальные переменные состояния
let userWallets =[];
let socket = null;
let productsMap = {}; // Кэш товаров для быстрого доступа при покупке
let selectedProductImage = null; // Храним выбранный файл картинки

// ==========================================
// ТОЧКА ВХОДА (ИНИЦИАЛИЗАЦИЯ)
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    if (window.currentUser) {
        initIbay();
    } else {
        document.addEventListener('UserDataLoaded', initIbay);
    }
});

async function initIbay() {
    await fetchWallets();
    await fetchProducts();
    fetchOrders();
    initWebSockets();

    document.getElementById('btnOpenCreateModal').addEventListener('click', () => {
        populateWalletSelect('prodWalletSelect');
        document.getElementById('modalCreateProduct').classList.remove('hidden');
    });

    // Слушатель для выбора файла картинки
    document.getElementById('prodPhotoInput').addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            selectedProductImage = e.target.files[0];
            document.getElementById('prodPhotoName').textContent = selectedProductImage.name;
        } else {
            selectedProductImage = null;
            document.getElementById('prodPhotoName').textContent = "Файл не выбран";
        }
    });

    document.getElementById('formCreateProduct').addEventListener('submit', handleCreateProduct);
    document.getElementById('formBuyProduct').addEventListener('submit', handleBuyProduct);
}


// ==========================================
// ФУНКЦИИ API И РЕНДЕРА
// ==========================================

async function fetchProducts() {
    try {
        const res = await fetch('/api/v1/ibay/products', {
            headers: { 'Authorization': `Bearer ${getCookie('access_token')}` }
        });
        const products = await res.json();

        const container = document.getElementById('productsView');
        container.innerHTML = '';
        productsMap = {};

        if (products.length === 0) {
            container.innerHTML = '<p style="padding: 10px;">Товаров пока нет.</p>';
            return;
        }

        products.forEach(p => {
            productsMap[p.id] = p;

            const imgUrl = p.photo_url || '/static/img/default-product.png';
            const safeTitle = escapeHTML(p.title);
            const safeAddress = escapeHTML(p.seller_address || '0x...');
            const displayPrice = parseFloat(p.price_eth).toString();

            const card = document.createElement('div');
            card.className = 'item-card-horizontal';
            card.innerHTML = `
                <img src="${escapeHTML(imgUrl)}" alt="Product" class="item-card-img" onerror="this.src='/static/img/default-product.png'">
                <div class="item-details">
                    <div class="item-row">
                        <span class="item-label">Title:</span>
                        <span class="item-value" style="font-size: 16px;">${safeTitle}</span>
                    </div>
                    <div class="item-row">
                        <span class="item-label">Address:</span>
                        <span class="item-value address">${safeAddress}</span>
                    </div>
                    <div class="item-row">
                        <span class="item-label">Price:</span>
                        <span class="item-value" style="font-size: 16px; color: #28a745; font-weight: bold;">${displayPrice} ETH</span>
                    </div>
                    <button class="btn btn-buy" onclick="openBuyModal('${p.id}')">Buy</button>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (error) {
        console.error('Error fetching products:', error);
        document.getElementById('productsView').innerHTML = '<p style="padding: 10px; color: red;">Ошибка загрузки товаров.</p>';
    }
}

async function fetchOrders() {
    try {
        const res = await fetch('/api/v1/ibay/orders', {
            headers: { 'Authorization': `Bearer ${getCookie('access_token')}` }
        });
        const orders = await res.json();
        const container = document.getElementById('ordersView');
        container.innerHTML = '';

        if (orders.length === 0) {
            container.innerHTML = '<p style="padding: 10px;">Вы еще ничего не заказывали.</p>';
            return;
        }

        orders.forEach(o => {
            const safeTx = escapeHTML(o.tx_hash);
            const safeStatus = escapeHTML(o.status);
            const safeRefundTx = o.return_tx_hash ? escapeHTML(o.return_tx_hash) : '';

            const d = o.created_at ? new Date(o.created_at) : new Date();
            const dateStr = d.toLocaleDateString('ru-RU', {day: '2-digit', month: '2-digit', year: 'numeric'}) + ' ' + d.toLocaleTimeString('ru-RU', {hour: '2-digit', minute:'2-digit'});

            const product = productsMap[o.product_id];
            const imgUrl = product && product.photo_url ? product.photo_url : '/static/img/default-product.png';
            const title = product ? product.title : `Товар #${o.id.substring(0,6)}`;
            const displayPrice = parseFloat(o.price_eth).toString();

            let displayStatus = safeStatus;
            let statusClass = safeStatus.toLowerCase();
            if (safeStatus === 'NEW' || safeStatus === 'PENDING') { displayStatus = 'Новый'; statusClass = 'new'; }
            if (safeStatus === 'DELIVERY') { displayStatus = 'Доставка'; statusClass = 'delivery'; }
            if (safeStatus === 'COMPLETED') { displayStatus = 'Завершено'; statusClass = 'completed'; }
            if (safeStatus === 'FAILED') { displayStatus = 'Провалено'; statusClass = 'failed'; }
            if (safeStatus === 'RETURNED') { displayStatus = 'Возврат'; statusClass = 'returned'; }

            const card = document.createElement('div');
            card.className = 'item-card-horizontal';
            card.innerHTML = `
                <img src="${escapeHTML(imgUrl)}" alt="Product" class="item-card-img" onerror="this.src='/static/img/default-product.png'">
                <div class="item-details">
                    <div class="item-row">
                        <span class="item-label">Название:</span>
                        <span class="item-value" style="font-size: 15px; font-weight: bold;">${escapeHTML(title)}</span>
                    </div>
                    <div class="item-row">
                        <span class="item-label">Транзакция:</span>
                        <span class="item-value address"><a href="https://sepolia.etherscan.io/tx/${safeTx}" target="_blank">${safeTx}</a></span>
                    </div>
                    <div class="item-row">
                        <span class="item-label">Цена:</span>
                        <span class="item-value" style="font-weight: bold;">${displayPrice} ETH</span>
                    </div>
                    <div class="item-row">
                        <span class="item-label">Время заказа:</span>
                        <span class="item-value">${dateStr}</span>
                    </div>
                    <div class="item-row">
                        <span class="item-label">Статус:</span>
                        <span class="item-value status-${statusClass}">${displayStatus}</span>
                    </div>
                    <div class="item-row">
                        <span class="item-label">Возврат:</span>
                        <span class="item-value address">
                            ${safeRefundTx ? `<a href="https://sepolia.etherscan.io/tx/${safeRefundTx}" target="_blank">${safeRefundTx}</a>` : '—'}
                        </span>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (error) {
        console.error('Error fetching orders:', error);
        document.getElementById('ordersView').innerHTML = '<p style="padding: 10px; color: red;">Ошибка загрузки заказов.</p>';
    }
}


// ==========================================
// ОБРАБОТЧИКИ ФОРМ (БИЗНЕС-ЛОГИКА S3)
// ==========================================

async function fetchWallets() {
    try {
        const res = await fetch('/api/v1/wallets', {
            headers: { 'Authorization': `Bearer ${getCookie('access_token')}` }
        });
        if (res.ok) {
            userWallets = await res.json();
        }
    } catch (e) {
        console.error('Error fetching wallets:', e);
    }
}

function populateWalletSelect(selectId) {
    const select = document.getElementById(selectId);
    select.innerHTML = '<option value="">Выберите кошелек...</option>';
    userWallets.forEach(w => {
        const opt = document.createElement('option');
        opt.value = w.id;
        opt.textContent = `${w.address} (${parseFloat(w.balance).toFixed(4)} ETH)`;
        select.appendChild(opt);
    });
}

async function handleCreateProduct(e) {
    e.preventDefault();
    const btnSubmit = e.target.querySelector('button[type="submit"]');
    btnSubmit.disabled = true;

    const title = document.getElementById('prodTitle').value;
    const price = document.getElementById('prodPrice').value;
    const walletId = document.getElementById('prodWalletSelect').value;

    let finalPhotoUrl = null;

    try {
        // --- ЛОГИКА ЗАГРУЗКИ В S3 ---
        if (selectedProductImage) {
            showNotification('Загрузка картинки в облако...', false);

            const extension = selectedProductImage.name.split('.').pop();
            const contentType = selectedProductImage.type;

            // 1. Получаем ссылку для загрузки (Presigned URL)
            const presignedRes = await fetch(`/api/v1/profile/me/avatar/presigned-url?extension=${extension}&content_type=${encodeURIComponent(contentType)}&file_type=products`, {
                headers: { 'Authorization': `Bearer ${getCookie('access_token')}` }
            });

            if (!presignedRes.ok) throw new Error("Не удалось получить ссылку для загрузки фото");
            const uploadData = await presignedRes.json();

            // 2. Отправляем файл напрямую в DigitalOcean Spaces
            const uploadRes = await fetch(uploadData.upload_url, {
                method: 'PUT',
                body: selectedProductImage,
                headers: {
                    'Content-Type': contentType,
                    'x-amz-acl': 'public-read' // Делаем файл публичным
                }
            });

            if (!uploadRes.ok) throw new Error("Ошибка при загрузке картинки в хранилище DO Spaces");

            // 3. Сохраняем публичный URL CDN
            finalPhotoUrl = uploadData.public_url;
        }

        // --- СОЗДАНИЕ ТОВАРА В БАЗЕ ---
        showNotification('Создание товара...', false);
        const res = await fetch('/api/v1/ibay/products', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getCookie('access_token')}`
            },
            body: JSON.stringify({
                title: title,
                price_eth: parseFloat(price),
                photo_url: finalPhotoUrl, // Передаем URL из S3
                wallet_id: walletId
            })
        });

        if (res.ok) {
            showNotification('Товар успешно опубликован!');
            closeModal('modalCreateProduct');
            document.getElementById('formCreateProduct').reset();

            // Сброс файла
            selectedProductImage = null;
            document.getElementById('prodPhotoName').textContent = 'Файл не выбран';

            fetchProducts();
        } else {
            const err = await res.json();
            throw new Error(err.detail || 'Ошибка публикации');
        }
    } catch (e) {
        showNotification(e.message || 'Сетевая ошибка', true);
    } finally {
        btnSubmit.disabled = false;
    }
}

async function handleBuyProduct(e) {
    e.preventDefault();
    const btnSubmit = e.target.querySelector('button[type="submit"]');
    btnSubmit.disabled = true;

    const productId = document.getElementById('buyProductId').value;
    const buyerWalletId = document.getElementById('buyWalletSelect').value;

    const product = productsMap[productId];
    if (!product) {
        showNotification('Ошибка данных товара. Обновите страницу.', true);
        btnSubmit.disabled = false;
        return;
    }

    try {
        showNotification('Отправка транзакции в сеть...', false);

        const txRes = await fetch('/api/v1/transactions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getCookie('access_token')}` },
            body: JSON.stringify({
                wallet_id: buyerWalletId,
                to_address: product.seller_address,
                value: parseFloat(product.price_eth)
            })
        });

        if (!txRes.ok) {
            const err = await txRes.json();
            throw new Error(err.detail || 'Ошибка при отправке транзакции');
        }

        const txData = await txRes.json();
        const realTxHash = txData.tx_hash;

        showNotification('Транзакция отправлена. Создаем заказ...', false);

        const res = await fetch('/api/v1/ibay/orders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getCookie('access_token')}` },
            body: JSON.stringify({
                product_id: productId,
                tx_hash: realTxHash,
                price_eth: parseFloat(product.price_eth)
            })
        });

        if (res.ok) {
            showNotification('Заказ оформлен! Ожидайте подтверждения сети.');
            closeModal('modalBuyProduct');
            fetchOrders();
        } else {
            const err = await res.json();
            throw new Error(err.detail || 'Ошибка оформления заказа');
        }
    } catch (e) {
        showNotification(e.message || 'Сетевая ошибка', true);
    } finally {
        btnSubmit.disabled = false;
    }
}

// ==========================================
// WEBSOCKETS И УТИЛИТЫ
// ==========================================

function initWebSockets() {
    const token = getCookie('access_token');
    if (!token) return;

    socket = io("/ibay", {
        auth: { token: token },
        transports: ['websocket', 'polling']
    });

    socket.on('ibay_order_updated', (data) => {
        const isError = data.status === 'FAILED' || data.status === 'RETURNED';
        showNotification(`Статус заказа изменен на: ${data.status}`, isError);
        fetchOrders();
    });

    socket.on('ibay_product_created', (data) => {
        fetchProducts();
    });
}

function openBuyModal(productId) {
    const product = productsMap[productId];
    if (!product) return;

    const displayPrice = parseFloat(product.price_eth).toString();

    document.getElementById('buyProductId').value = productId;
    document.getElementById('buyTitle').textContent = product.title;
    document.getElementById('buyPrice').textContent = `${displayPrice} ETH`;

    populateWalletSelect('buyWalletSelect');
    document.getElementById('modalBuyProduct').classList.remove('hidden');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
    // Очистка при закрытии
    if(modalId === 'modalCreateProduct') {
        document.getElementById('formCreateProduct').reset();
        selectedProductImage = null;
        document.getElementById('prodPhotoName').textContent = 'Файл не выбран';
    }
}

function escapeHTML(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function showNotification(message, isError = false) {
    const toast = document.createElement('div');
    toast.textContent = message;

    Object.assign(toast.style, {
        position: 'fixed', bottom: '20px', right: '20px', padding: '15px 25px',
        background: isError ? '#e74c3c' : '#2ecc71', color: 'white',
        borderRadius: '5px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        zIndex: '9999', transition: 'opacity 0.3s ease-in-out',
        fontWeight: 'bold', fontSize: '14px'
    });

    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);

    let token = null;
    if (parts.length === 2) {
        token = parts.pop().split(';').shift();
    }
    if (!token) {
        token = localStorage.getItem('access_token');
    }
    if (token) {
        token = decodeURIComponent(token).replace(/^bearer\s+/i, '').trim();
    }
    return token;
}

// Глобальные переменные
let currentWallets = [];
let balancePollInterval = null; // Переменная для таймера AJAX-запросов баланса

// НОВЫЕ ПЕРЕМЕННЫЕ ДЛЯ МОДАЛКИ ИСТОРИИ ТРАНЗАКЦИЙ:
let txPollInterval = null;
let currentOpenWalletId = null;

document.addEventListener('DOMContentLoaded', () => {
    loadWallets();

    // Запускаем фоновое обновление балансов каждые 30 секунд
    balancePollInterval = setInterval(updateBalances, 30000);

    // Обработчик отправки транзакции
    const btnSend = document.getElementById('btnSendTx');

    btnSend.addEventListener('click', async () => {
        const walletId = document.getElementById('sendFromWalletId').value;
        const toAddress = document.getElementById('sendToAddress').value.trim();
        const value = document.getElementById('sendValue').value;
        const resultDiv = document.getElementById('sendTxResult');

        if (!toAddress || !toAddress.startsWith('0x') || toAddress.length !== 42) {
            alert('Пожалуйста, введите корректный адрес Ethereum (начинается с 0x, 42 символа).');
            return;
        }

        if (!value || value <= 0) {
            alert('Пожалуйста, введите корректную сумму.');
            return;
        }

        btnSend.disabled = true;
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = '<span style="color: #f39c12;">Отправка транзакции...</span>';

        try {
            const res = await fetch('/api/v1/transactions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    wallet_id: walletId,
                    to_address: toAddress,
                    value: parseFloat(value)
                })
            });

            const data = await res.json();

            if (res.ok) {
                resultDiv.innerHTML = `
                    <span style="color: #27ae60; font-weight: bold;">Отправка произведена. Ожидайте подтверждения сети...</span><br>
                    <a href="https://sepolia.etherscan.io/tx/${data.tx_hash || data.hash}" target="_blank" style="color: #3498db;">Ссылка на транзакцию</a>
                `;
                document.getElementById('sendToAddress').value = '';
                document.getElementById('sendValue').value = '';

                // Форсируем обновление балансов через 5 и 10 секунд после успешной отправки
                setTimeout(updateBalances, 5000);
                setTimeout(updateBalances, 10000);
            } else {
                let errorMsg = "Неизвестная ошибка";
                if (data.detail) {
                    errorMsg = Array.isArray(data.detail) ? data.detail[0].msg : data.detail;
                }
                resultDiv.innerHTML = `<span style="color: #e74c3c;">Ошибка: ${errorMsg}</span>`;
            }
        } catch (e) {
            resultDiv.innerHTML = `<span style="color: #e74c3c;">Ошибка сети.</span>`;
        } finally {
            btnSend.disabled = false;
        }
    });
});

// --- ФОНОВОЕ ОБНОВЛЕНИЕ БАЛАНСОВ (AJAX) ---
async function updateBalances() {
    if (!currentWallets || currentWallets.length === 0) return;

    currentWallets.forEach(async (wallet) => {
        try {
            const balRes = await fetch(`/api/v1/wallets/${wallet.id}/balance`);
            if (balRes.ok) {
                const balData = await balRes.json();
                const balanceSpan = document.getElementById(`balance-${wallet.id}`);

                if (balanceSpan) {
                    const currentText = balanceSpan.textContent;
                    const newText = parseFloat(balData.balance).toFixed(4);

                    // Если баланс изменился (и это не первичная загрузка), делаем красивую зеленую подсветку
                    if (currentText !== newText && currentText !== 'Загрузка...') {
                        balanceSpan.style.color = '#27ae60';
                        balanceSpan.style.fontWeight = 'bold';
                        setTimeout(() => {
                            balanceSpan.style.color = '';
                            balanceSpan.style.fontWeight = 'normal';
                        }, 2000);
                    }

                    balanceSpan.textContent = newText;
                }
            }
        } catch (e) {
            console.error(`Ошибка фонового обновления баланса для ${wallet.id}`, e);
        }
    });
}

// Загрузка кошельков
async function loadWallets() {
    const container = document.getElementById('walletsContainer');
    try {
        const res = await fetch('/api/v1/wallets');

        if (res.status === 401 || res.status === 403) {
            window.location.href = "/login";
            return;
        }

        if (res.ok) {
            currentWallets = await res.json();
            container.innerHTML = '';

            if (currentWallets.length === 0) {
                container.innerHTML = '<div style="color: #888;">У вас нет кошельков. Создайте их в профиле.</div>';
                return;
            }

            currentWallets.forEach(wallet => {
                const card = document.createElement('div');
                card.className = 'wallet-card';
                card.innerHTML = `
                    <div class="wallet-header">
                        <div style="font-size: 30px; color: #627eea;">⟠</div>
                        <div class="wallet-info">
                            <div class="wallet-label">Адрес:</div>
                            <a href="https://sepolia.etherscan.io/address/${wallet.address}" target="_blank" class="wallet-address">${wallet.address}</a>
                            <div class="wallet-balance"><span id="balance-${wallet.id}" style="transition: color 0.3s;">Загрузка...</span> ETH</div>
                        </div>
                    </div>
                    <div class="wallet-actions">
                        <button class="btn-wallet btn-watch" onclick="openTxHistory('${wallet.id}', '${wallet.address}')">Watch Transactions</button>
                        <button class="btn-wallet btn-send" onclick="openSendModal('${wallet.id}')">Send Transaction</button>
                        <button class="btn-wallet btn-faucet" onclick="requestFaucet('${wallet.id}')">Get Test ETH</button>
                    </div>
                `;
                container.appendChild(card);
            });

            // Сразу же запрашиваем балансы первый раз после отрисовки карточек
            updateBalances();
        }
    } catch (e) {
        container.innerHTML = '<div style="color: red;">Ошибка загрузки кошельков.</div>';
    }
}

// Открытие модалки отправки
window.openSendModal = (walletId) => {
    document.getElementById('sendFromWalletId').value = walletId;
    document.getElementById('sendTxResult').style.display = 'none';
    document.getElementById('sendTxModal').style.display = 'flex';
};

// Запрос в фаусет
window.requestFaucet = async (walletId) => {
    showGlobalAlert('Запрос отправлен в Faucet. Ожидайте подтверждения...', false);
    try {
        const res = await fetch(`/api/v1/faucet/${walletId}/request-eth`, { method: 'POST' });

        const contentType = res.headers.get("content-type");
        let data = null;
        if (contentType && contentType.includes("application/json")) {
            data = await res.json();
        }

        if (res.ok) {
            showGlobalAlert('ETH успешно запрошен! Баланс обновится автоматически в течение минуты.');

            // Запускаем серию проверок баланса через интервалы
            setTimeout(updateBalances, 5000);  // через 5 секунд
            setTimeout(updateBalances, 15000); // через 15 секунд
            setTimeout(updateBalances, 30000); // через 30 секунд
        } else {
            let errorMsg = data && data.detail ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)) : `Ошибка сервера (Код ${res.status})`;
            showGlobalAlert(`Ошибка Faucet: ${errorMsg}`, true);
        }
    } catch (e) {
        console.error("Ошибка Faucet:", e);
        showGlobalAlert('Сбой сети или сервер не отвечает при запросе Faucet', true);
    }
};

// --- НОВАЯ ЛОГИКА ИСТОРИИ ТРАНЗАКЦИЙ (ЖИВОЕ ОБНОВЛЕНИЕ) ---

// 1. Открытие модалки истории и запуск опроса
window.openTxHistory = (walletId, address) => {
    currentOpenWalletId = walletId;
    document.getElementById('txHistoryTitle').textContent = `История транзакций ${address.substring(0,8)}...`;
    const tbody = document.getElementById('txTableBody');

    // Показываем "Загрузку" только при первом открытии
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">Загрузка...</td></tr>';
    document.getElementById('txHistoryModal').style.display = 'flex';

    // Делаем первый мгновенный запрос
    fetchAndUpdateTxs(walletId);

    // Запускаем фоновое обновление каждые 10 секунд (пока открыта модалка)
    if (txPollInterval) clearInterval(txPollInterval);
    txPollInterval = setInterval(() => {
        fetchAndUpdateTxs(walletId);
    }, 10000);
};

// 2. Умная функция обновления (без моргания таблицы)
async function fetchAndUpdateTxs(walletId) {
    // Если пользователь уже закрыл модалку или переключился, прерываемся
    if (currentOpenWalletId !== walletId) return;

    const tbody = document.getElementById('txTableBody');

    try {
        const res = await fetch(`/api/v1/transactions/wallet/${walletId}`);
        if (!res.ok) return;

        const txs = await res.json();

        // Убираем надпись "Загрузка" или "Транзакций не найдено", если пришли данные
        if (tbody.children.length === 1 && tbody.children[0].cells.length === 1 && txs.length > 0) {
            tbody.innerHTML = '';
        }

        // Если список пуст
        if (txs.length === 0 && (tbody.innerHTML === '' || tbody.children[0].cells.length === 1)) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">Транзакций не найдено.</td></tr>';
            return;
        }

        txs.forEach((tx, index) => {
            const isError = tx.isError === "1" || tx.status === "failed";
            const isPending = tx.status === "pending";

            let statusHtml = '<span style="color: #27ae60; font-weight: bold;">Success</span>';
            if (isError) statusHtml = '<span style="color: #e74c3c; font-weight: bold;">Failed</span>';
            if (isPending) statusHtml = '<span style="color: #f39c12; font-weight: bold;">Pending ⏳</span>';

            // Ищем, есть ли уже эта транзакция в таблице (по id строки)
            const existingRow = document.getElementById(`tx-row-${tx.hash}`);

            if (existingRow) {
                // ТРАНЗАКЦИЯ УЖЕ ЕСТЬ: проверяем, не изменился ли статус
                const statusCell = document.getElementById(`tx-status-${tx.hash}`);
                if (statusCell && statusCell.innerHTML !== statusHtml) {
                    statusCell.innerHTML = statusHtml;

                    // Делаем зеленую вспышку, чтобы привлечь внимание к успешной транзакции
                    existingRow.style.backgroundColor = 'rgba(39, 174, 96, 0.2)';
                    existingRow.style.transition = 'background-color 1s ease';
                    setTimeout(() => existingRow.style.backgroundColor = '', 1500);

                    // Транзакция подтвердилась - форсируем обновление балансов
                    updateBalances();
                }
            } else {
                // НОВАЯ ТРАНЗАКЦИЯ: создаем её
                const valEth = (parseFloat(tx.value) / 1e18).toFixed(4);
                const date = tx.timeStamp ? new Date(tx.timeStamp * 1000).toLocaleString() : '---';

                const newRow = document.createElement('tr');
                newRow.id = `tx-row-${tx.hash}`;
                newRow.innerHTML = `
                    <td><a href="https://sepolia.etherscan.io/tx/${tx.hash}" target="_blank" style="color: #3498db;">${tx.hash.substring(0, 10)}...</a></td>
                    <td>${date}</td>
                    <td title="${tx.from}">${tx.from.substring(0, 8)}...</td>
                    <td title="${tx.to}">${tx.to.substring(0, 8)}...</td>
                    <td><strong>${valEth}</strong> ETH</td>
                    <td id="tx-status-${tx.hash}">${statusHtml}</td>
                `;

                // Вставляем её в правильное место, чтобы сохранить сортировку от новых к старым
                if (index >= tbody.children.length) {
                    tbody.appendChild(newRow);
                } else {
                    tbody.insertBefore(newRow, tbody.children[index]);
                }

                // Делаем синюю вспышку для новой появившейся транзакции
                newRow.style.backgroundColor = 'rgba(52, 152, 219, 0.2)';
                newRow.style.transition = 'background-color 1s ease';
                setTimeout(() => newRow.style.backgroundColor = '', 1500);
            }
        });

    } catch (e) {
        console.error("Ошибка при фоновом обновлении транзакций:", e);
    }
}

// Закрытие модалок
window.closeModal = (id) => {
    document.getElementById(id).style.display = 'none';

    // Если закрываем модалку истории - чистим таймер
    if (id === 'txHistoryModal') {
        if (txPollInterval) {
            clearInterval(txPollInterval);
            txPollInterval = null;
        }
        currentOpenWalletId = null; // Сбрасываем ID
    }
};

function showGlobalAlert(message, isError = false) {
    const alertDiv = document.getElementById('globalAlert');
    if (!alertDiv) {
        alert(message);
        return;
    }
    alertDiv.style.display = 'block';
    alertDiv.style.backgroundColor = isError ? '#f8d7da' : '#d4edda';
    alertDiv.style.color = isError ? '#721c24' : '#155724';
    alertDiv.style.padding = '10px';
    alertDiv.style.borderRadius = '5px';
    alertDiv.style.marginBottom = '15px';
    alertDiv.style.border = isError ? '1px solid #f5c6cb' : '1px solid #c3e6cb';
    alertDiv.textContent = message;

    setTimeout(() => { alertDiv.style.display = 'none'; }, 7000);
}

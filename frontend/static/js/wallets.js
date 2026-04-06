// Глобальные переменные
let currentWallets = [];
let balancePollInterval = null;

let txPollInterval = null;
let currentOpenWalletId = null;

// --- МАГИЯ СИНХРОНИЗАЦИИ ВКЛАДОК ---
// Создаем канал связи между всеми открытыми вкладками нашего сайта
const txChannel = new BroadcastChannel('wallet_tx_channel');

// Слушаем сообщения от ДРУГИХ вкладок
txChannel.onmessage = (event) => {
    const data = event.data;
    if (data.type === 'NEW_PENDING_TX') {
        // Если в этой вкладке открыта модалка именно этого кошелька - мгновенно рисуем транзакцию
        if (currentOpenWalletId === data.walletId) {
            injectPendingTxToUI(data.walletId, data.txHash, data.fromAddr, data.toAddr, data.valueEth);
        }
        // В любом случае запускаем таймеры обновления балансов, так как транзакция пошла
        setTimeout(updateBalances, 5000);
        setTimeout(updateBalances, 15000);
    }
};
// -----------------------------------

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

            const responseData = await res.json();

            if (res.ok) {
                const txHash = responseData.tx_hash || responseData.hash || `pending_${Date.now()}`;
                const wallet = currentWallets.find(w => w.id === walletId);
                const fromAddress = wallet ? wallet.address : 'Ваш кошелек';

                // Сбрасываем форму и закрываем модалку отправки
                document.getElementById('sendToAddress').value = '';
                document.getElementById('sendValue').value = '';
                closeModal('sendTxModal');

                // Автоматически открываем модалку истории в ЭТОЙ вкладке
                openTxHistory(walletId, fromAddress);

                // МГНОВЕННО инжектим транзакцию в ЭТУ вкладку
                injectPendingTxToUI(walletId, txHash, fromAddress, toAddress, value);

                // РАССЫЛАЕМ УВЕДОМЛЕНИЕ ДРУГИМ ВКЛАДКАМ
                txChannel.postMessage({
                    type: 'NEW_PENDING_TX',
                    walletId: walletId,
                    txHash: txHash,
                    fromAddr: fromAddress,
                    toAddr: toAddress,
                    valueEth: value
                });

                showGlobalAlert('Транзакция отправлена в сеть! Ожидайте подтверждения...');

                setTimeout(updateBalances, 5000);
                setTimeout(updateBalances, 10000);
            } else {
                let errorMsg = "Неизвестная ошибка";
                if (responseData.detail) {
                    errorMsg = Array.isArray(responseData.detail) ? responseData.detail[0].msg : responseData.detail;
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

            updateBalances();
        }
    } catch (e) {
        container.innerHTML = '<div style="color: red;">Ошибка загрузки кошельков.</div>';
    }
}

window.openSendModal = (walletId) => {
    document.getElementById('sendFromWalletId').value = walletId;
    document.getElementById('sendTxResult').style.display = 'none';
    document.getElementById('sendTxModal').style.display = 'flex';
};

window.requestFaucet = async (walletId) => {
    showGlobalAlert('Запрос отправлен в Faucet. Ожидайте...', false);

    const wallet = currentWallets.find(w => w.id === walletId);
    const address = wallet ? wallet.address : '';

    // Сразу открываем модалку истории для наглядности в ЭТОЙ вкладке
    openTxHistory(walletId, address);

    try {
        const res = await fetch(`/api/v1/faucet/${walletId}/request-eth`, { method: 'POST' });

        const contentType = res.headers.get("content-type");
        let data = null;
        if (contentType && contentType.includes("application/json")) {
            data = await res.json();
        }

        if (res.ok) {
            showGlobalAlert('ETH успешно запрошен! Баланс обновится автоматически в течение минуты.');

            const txHash = typeof data === 'string' ? data : (data?.tx_hash || data?.hash || `faucet_${Date.now()}`);

            // Мгновенно инжектим в ЭТУ вкладку
            injectPendingTxToUI(walletId, txHash, 'Faucet', address, '0.001');

            // РАССЫЛАЕМ УВЕДОМЛЕНИЕ ДРУГИМ ВКЛАДКАМ
            txChannel.postMessage({
                type: 'NEW_PENDING_TX',
                walletId: walletId,
                txHash: txHash,
                fromAddr: 'Faucet',
                toAddr: address,
                valueEth: '0.001'
            });

            setTimeout(updateBalances, 5000);
            setTimeout(updateBalances, 15000);
            setTimeout(updateBalances, 30000);
        } else {
            let errorMsg = data && data.detail ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)) : `Ошибка сервера (Код ${res.status})`;
            showGlobalAlert(`Ошибка Faucet: ${errorMsg}`, true);
        }
    } catch (e) {
        showGlobalAlert('Сбой сети или сервер не отвечает при запросе Faucet', true);
    }
};

// --- ИСТОРИЯ ТРАНЗАКЦИЙ ---

// Функция для МГНОВЕННОГО отображения транзакции после клика (до того как отработает API)
function injectPendingTxToUI(walletId, txHash, fromAddr, toAddr, valueEth) {
    if (currentOpenWalletId !== walletId) return;

    const tbody = document.getElementById('txTableBody');
    if (tbody.children.length === 1 && tbody.children[0].cells.length === 1) {
        tbody.innerHTML = ''; // Убираем "Загрузка..."
    }

    const safeHashId = txHash.toLowerCase();
    if (document.getElementById(`tx-row-${safeHashId}`)) return;

    const date = new Date().toLocaleString();
    const newRow = document.createElement('tr');
    newRow.id = `tx-row-${safeHashId}`;
    newRow.setAttribute('data-injected-at', Date.now().toString());

    const hashDisplay = txHash.startsWith('0x')
        ? `<a href="https://sepolia.etherscan.io/tx/${txHash}" target="_blank" style="color: #3498db;">${txHash.substring(0, 10)}...</a>`
        : `<span style="color: #888;" title="Ожидание формирования хэша">${txHash.substring(0, 10)}...</span>`;

    newRow.innerHTML = `
        <td>${hashDisplay}</td>
        <td>${date}</td>
        <td title="${fromAddr}">${fromAddr.substring(0, 8)}...</td>
        <td title="${toAddr}">${toAddr.substring(0, 8)}...</td>
        <td><strong>${parseFloat(valueEth).toFixed(4)}</strong> ETH</td>
        <td id="tx-status-${safeHashId}" data-status="pending"><span style="color: #f39c12; font-weight: bold;">Pending ⏳</span></td>
    `;

    tbody.insertBefore(newRow, tbody.firstChild);

    newRow.style.backgroundColor = 'rgba(243, 156, 18, 0.2)';
    newRow.style.transition = 'background-color 1s ease';
    setTimeout(() => newRow.style.backgroundColor = '', 1500);
}

window.openTxHistory = (walletId, address) => {
    currentOpenWalletId = walletId;
    document.getElementById('txHistoryTitle').textContent = `История транзакций ${address.substring(0,8)}...`;
    const tbody = document.getElementById('txTableBody');

    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">Загрузка...</td></tr>';
    document.getElementById('txHistoryModal').style.display = 'flex';

    fetchAndUpdateTxs(walletId);

    if (txPollInterval) clearInterval(txPollInterval);
    txPollInterval = setInterval(() => {
        fetchAndUpdateTxs(walletId);
    }, 10000);
};

async function fetchAndUpdateTxs(walletId) {
    if (currentOpenWalletId !== walletId) return;
    const tbody = document.getElementById('txTableBody');

    try {
        const res = await fetch(`/api/v1/transactions/wallet/${walletId}`);
        if (!res.ok) return;

        const txs = await res.json();

        if (tbody.children.length === 1 && tbody.children[0].cells.length === 1 && txs.length > 0) {
            tbody.innerHTML = '';
        }

        if (txs.length === 0 && (tbody.innerHTML === '' || tbody.children[0].cells.length === 1)) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">Транзакций не найдено.</td></tr>';
            return;
        }

        // УДАЛЕНИЕ "ПРИЗРАЧНЫХ" СТРОК
        const currentHashes = new Set(txs.map(tx => (tx.hash || tx.tx_hash).toLowerCase()));
        const rows = tbody.querySelectorAll('tr[id^="tx-row-"]');

        rows.forEach(row => {
            const rowHash = row.id.replace('tx-row-', '');
            if (!currentHashes.has(rowHash)) {
                const injectedAt = row.getAttribute('data-injected-at');
                if (injectedAt && (Date.now() - parseInt(injectedAt) < 60000)) {
                    return;
                }
                row.remove();
            }
        });

        txs.forEach((tx, index) => {
            const txHash = tx.hash || tx.tx_hash;
            if (!txHash) return;

            const rawStatus = String(tx.status || "").toLowerCase();
            const isError = tx.isError === "1" || tx.txreceipt_status === "0" || rawStatus === "failed" || rawStatus === "error";
            const isSuccess = tx.txreceipt_status === "1" || rawStatus === "success" || (tx.blockNumber && parseInt(tx.blockNumber) > 0 && !isError);
            const isPending = !isError && !isSuccess && (rawStatus === "pending" || !tx.blockNumber);

            let statusHtml = '<span style="color: #27ae60; font-weight: bold;">Success</span>';
            let statusCode = 'success';

            if (isError) {
                statusHtml = '<span style="color: #e74c3c; font-weight: bold;">Failed</span>';
                statusCode = 'failed';
            } else if (isPending) {
                statusHtml = '<span style="color: #f39c12; font-weight: bold;">Pending ⏳</span>';
                statusCode = 'pending';
            }

            const safeHashId = txHash.toLowerCase();
            const rowId = `tx-row-${safeHashId}`;
            const existingRow = document.getElementById(rowId);

            if (existingRow) {
                const statusCell = document.getElementById(`tx-status-${safeHashId}`);
                const currentStatus = statusCell ? statusCell.getAttribute('data-status') : null;

                if (statusCell && currentStatus !== statusCode) {
                    statusCell.innerHTML = statusHtml;
                    statusCell.setAttribute('data-status', statusCode);

                    existingRow.style.backgroundColor = statusCode === 'success' ? 'rgba(39, 174, 96, 0.2)' : 'rgba(231, 76, 60, 0.2)';
                    existingRow.style.transition = 'background-color 1s ease';
                    setTimeout(() => existingRow.style.backgroundColor = '', 1500);

                    if (statusCode === 'success') {
                        updateBalances();
                    }
                }
            } else {
                let valNum = parseFloat(tx.value || 0);
                if (valNum > 1000000000) valNum = valNum / 1e18;
                const valEth = valNum.toFixed(4);

                const date = tx.timeStamp ? new Date(tx.timeStamp * 1000).toLocaleString() : '---';
                const fromAddr = tx.from || tx.from_address || '---';
                const toAddr = tx.to || tx.to_address || '---';

                const newRow = document.createElement('tr');
                newRow.id = rowId;

                const hashDisplay = txHash.startsWith('0x')
                    ? `<a href="https://sepolia.etherscan.io/tx/${txHash}" target="_blank" style="color: #3498db;">${txHash.substring(0, 10)}...</a>`
                    : `<span style="color: #888;" title="Ожидание формирования хэша">${txHash.substring(0, 10)}...</span>`;

                newRow.innerHTML = `
                    <td>${hashDisplay}</td>
                    <td>${date}</td>
                    <td title="${fromAddr}">${fromAddr.substring(0, 8)}...</td>
                    <td title="${toAddr}">${toAddr.substring(0, 8)}...</td>
                    <td><strong>${valEth}</strong> ETH</td>
                    <td id="tx-status-${safeHashId}" data-status="${statusCode}">${statusHtml}</td>
                `;

                if (index >= tbody.children.length) {
                    tbody.appendChild(newRow);
                } else {
                    tbody.insertBefore(newRow, tbody.children[index]);
                }

                newRow.style.backgroundColor = 'rgba(52, 152, 219, 0.2)';
                newRow.style.transition = 'background-color 1s ease';
                setTimeout(() => newRow.style.backgroundColor = '', 1500);
            }
        });

    } catch (e) {
        console.error("Ошибка при фоновом обновлении транзакций:", e);
    }
}

window.closeModal = (id) => {
    document.getElementById(id).style.display = 'none';

    if (id === 'txHistoryModal') {
        if (txPollInterval) {
            clearInterval(txPollInterval);
            txPollInterval = null;
        }
        currentOpenWalletId = null;
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

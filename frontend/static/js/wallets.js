let currentWallets =[];
let currentOpenWalletId = null;
let walletSocket = null;
window.waitingForWalletTx = null;

let currentModalTxs =[];
let currentSortCol = 'age';
let currentSortAsc = false; // По умолчанию сортируем от новых к старым (DESC)

function getCookie(name) {
    let matches = document.cookie.match(new RegExp(
        "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
    ));
    return matches ? decodeURIComponent(matches[1]) : undefined;
}

function timeAgo(timestampSeconds) {
    if (!timestampSeconds || timestampSeconds === "0" || timestampSeconds === 0) {
        return '<span style="color:#f39c12">Pending...</span>';
    }
    const seconds = Math.floor(Date.now() / 1000) - parseInt(timestampSeconds);
    if (seconds < 0) return `0 secs ago`; // Защита от опережения времени сервера
    if (seconds < 60) return `${seconds} secs ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} mins ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hrs ago`;
    const days = Math.floor(hours / 24);
    return `${days} days ago`;
}

function getTxFee(tx) {
    if (tx.tx_fee) return parseFloat(tx.tx_fee);
    if (tx.gasUsed && tx.gasPrice) return (parseFloat(tx.gasUsed) * parseFloat(tx.gasPrice)) / 1e18;
    return 0;
}

function getStatusVal(tx) {
    const rawStatus = String(tx.status || "").toLowerCase();
    const isError = tx.isError === "1" || tx.txreceipt_status === "0" || rawStatus === "failed" || rawStatus === "error";
    const isSuccess = tx.txreceipt_status === "1" || rawStatus === "success" || (tx.blockNumber && parseInt(tx.blockNumber) > 0 && !isError);
    if (isSuccess) return 2;
    if (isError) return 0;
    return 1; // 1 - это Pending
}

const txChannel = new BroadcastChannel('wallet_tx_channel');
txChannel.onmessage = (event) => {
    const data = event.data;
    if (data.type === 'NEW_PENDING_TX') {
        if (currentOpenWalletId === data.walletId) {
            fetchAndUpdateTxs(data.walletId);
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    loadWallets();
    initWalletSocket();

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
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getCookie('access_token')}` },
                body: JSON.stringify({
                    wallet_id: walletId,
                    to_address: toAddress,
                    value: parseFloat(value)
                })
            });

            const textResponse = await res.text();
            let responseData = {};
            try { responseData = JSON.parse(textResponse); } catch(err) { responseData = { detail: "Ошибка сервера" }; }

            if (res.ok) {
                document.getElementById('sendToAddress').value = '';
                document.getElementById('sendValue').value = '';
                closeModal('sendTxModal');

                // Устанавливаем currentOpenWalletId сразу, чтобы WS-события
                // и fetchAndUpdateTxs работали даже без открытой истории
                currentOpenWalletId = walletId;

                // Инжектим pending-запись мгновенно — не ждём ответа от сервера
                const pendingEntry = {
                    hash: responseData.tx_hash || `pending_${Date.now()}`,
                    from: responseData.from_address || '---',
                    to: responseData.to_address || '---',
                    value: String(Math.round((parseFloat(value) || 0) * 1e18)),
                    timeStamp: Math.floor(Date.now() / 1000).toString(),
                    status: 'pending',
                    tx_fee: '0',
                    isError: '0'
                };
                currentModalTxs.unshift(pendingEntry);

                document.getElementById('txStatusIcon').textContent = '⏳';
                document.getElementById('txStatusText').textContent = 'Ожидание сети...';
                document.getElementById('txStatusText').style.color = '#f39c12';
                document.getElementById('txStatusLink').innerHTML = '<span style="color: #888;">Формирование хэша...</span>';
                document.getElementById('txStatusModal').style.display = 'flex';

                window.waitingForWalletTx = walletId;
                // Теперь fetchAndUpdateTxs не вернётся досрочно — currentOpenWalletId совпадает
                fetchAndUpdateTxs(walletId);
            } else {
                let errorMsg = responseData.detail ? (Array.isArray(responseData.detail) ? responseData.detail[0].msg : responseData.detail) : "Неизвестная ошибка";
                resultDiv.innerHTML = `<span style="color: #e74c3c;">Ошибка: ${errorMsg}</span>`;
            }
        } catch (e) {
            resultDiv.innerHTML = `<span style="color: #e74c3c;">Сетевая ошибка: сервер недоступен.</span>`;
        } finally {
            btnSend.disabled = false;
        }
    });
});

function initWalletSocket() {
    if (typeof io === 'undefined') return;
    const token = getCookie('access_token');
    if (!token) return;

    walletSocket = io("/transaction", { auth: { token: token }, transports: ['websocket'] });

    walletSocket.on("transaction_status_changed", (data) => {
        const safeHashId = (data.tx_hash || "").toLowerCase();
        const statusStr = String(data.status).toLowerCase();

        // 1. Оптимистичное обновление таблицы транзакций на лету
        if (currentOpenWalletId && (String(currentOpenWalletId) === String(data.wallet_id) || !data.wallet_id)) {

            // Ищем транзакцию по новому хэшу
            let tx = currentModalTxs.find(t => (t.hash || t.tx_hash || t.id || "").toLowerCase() === safeHashId);

            // Если транзакция всё еще имеет временный ID (pending_uuid), ищем её и обновляем хэш
            if (!tx) {
                tx = currentModalTxs.find(t => {
                    const h = (t.hash || t.tx_hash || t.id || "").toLowerCase();
                    return !h.startsWith('0x') && String(t.status).toLowerCase() === 'pending';
                });
            }

            if (tx) {
                // Обновляем статус и хэш существующей записи
                tx.hash = data.tx_hash;
                tx.status = statusStr;
                if (data.value) tx.value = data.value;
                if (statusStr === 'failed') tx.isError = "1";
                if (statusStr === 'success') tx.txreceipt_status = "1";
            } else {
                // Если вообще не нашли — мгновенно вставляем новую строку Pending
                currentModalTxs.unshift({
                    hash: data.tx_hash,
                    from: '---',
                    to: '---',
                    value: data.value || '0',
                    timeStamp: Math.floor(Date.now() / 1000).toString(),
                    status: statusStr,
                    tx_fee: '0',
                    isError: statusStr === 'failed' ? "1" : "0"
                });
            }

            // Перерисовываем UI мгновенно
            applySortAndRender();

            // Запрашиваем полный список с бэкенда тихо в фоне для точных данных
            fetchAndUpdateTxs(currentOpenWalletId);
        }

        // 2. Обновление модалки отправки (если она открыта)
        if (window.waitingForWalletTx && String(window.waitingForWalletTx) === String(data.wallet_id)) {
            const textDiv = document.getElementById('txStatusText');
            const iconDiv = document.getElementById('txStatusIcon');
            const linkDiv = document.getElementById('txStatusLink');

            if (data.tx_hash && data.tx_hash.startsWith('0x')) {
                linkDiv.innerHTML = `<a href="https://sepolia.etherscan.io/tx/${data.tx_hash}" target="_blank" style="color: #3498db; text-decoration: none; font-weight: bold;">Посмотреть транзакцию в Etherscan ↗</a>`;
            }

            if (statusStr === 'success' || statusStr === '1') {
                iconDiv.textContent = '✅';
                textDiv.textContent = 'Транзакция успешно завершена!';
                textDiv.style.color = '#27ae60';
                window.waitingForWalletTx = null;
            } else if (statusStr === 'failed' || statusStr === '0') {
                iconDiv.textContent = '❌';
                textDiv.textContent = 'Ошибка транзакции';
                textDiv.style.color = '#e74c3c';
                window.waitingForWalletTx = null;
            }
        }

        if (statusStr === 'success' || statusStr === '1') {
            showGlobalAlert(`Транзакция ${data.tx_hash ? data.tx_hash.substring(0,10) : '...'} успешно завершена!`);
        } else if (statusStr === 'failed' || statusStr === '0') {
            showGlobalAlert(`Транзакция завершилась ошибкой`, true);
        }
    });

    walletSocket.on("balance_updated", (data) => {
        const balanceSpan = document.getElementById(`balance-${data.wallet_id}`);
        if (balanceSpan) {
            const newText = parseFloat(data.balance).toFixed(4);
            if (balanceSpan.textContent !== newText) {
                balanceSpan.style.color = '#27ae60';
                balanceSpan.style.fontWeight = 'bold';
                setTimeout(() => { balanceSpan.style.color = ''; balanceSpan.style.fontWeight = ''; }, 2000);
                balanceSpan.textContent = newText;
            }
        }
    });
}

async function loadWallets() {
    const container = document.getElementById('walletsContainer');
    try {
        const res = await fetch('/api/v1/wallets', { headers: { 'Authorization': `Bearer ${getCookie('access_token')}` } });
        if (res.ok) {
            currentWallets = await res.json();
            container.innerHTML = '';
            if (currentWallets.length === 0) {
                container.innerHTML = '<div style="color: #888;">У вас нет кошельков. Создайте их в профиле.</div>';
                return;
            }
            currentWallets.forEach(wallet => {
                const balanceFromDB = parseFloat(wallet.balance || 0).toFixed(4);
                const card = document.createElement('div');
                card.className = 'wallet-card';
                card.innerHTML = `
                    <div class="wallet-header">
                        <div style="font-size: 30px; color: #627eea;">⟠</div>
                        <div class="wallet-info">
                            <div class="wallet-label">Адрес:</div>
                            <a href="https://sepolia.etherscan.io/address/${wallet.address}" target="_blank" class="wallet-address">${wallet.address}</a>
                            <div class="wallet-balance"><span id="balance-${wallet.id}" style="transition: color 0.3s;">${balanceFromDB}</span> ETH</div>
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
    try {
        const res = await fetch(`/api/v1/faucet/${walletId}/request-eth`, { method: 'POST', headers: { 'Authorization': `Bearer ${getCookie('access_token')}` } });
        if (res.ok) {
            showGlobalAlert('ETH успешно запрошен! Ожидайте подтверждения сети.');

            // Аналогично отправке — выставляем walletId и инжектим pending
            currentOpenWalletId = walletId;
            currentModalTxs.unshift({
                hash: `pending_faucet_${Date.now()}`,
                from: 'Faucet',
                to: '---',
                value: '0',
                timeStamp: Math.floor(Date.now() / 1000).toString(),
                status: 'pending',
                tx_fee: '0',
                isError: '0'
            });

            document.getElementById('txStatusIcon').textContent = '⏳';
            document.getElementById('txStatusText').textContent = 'Ожидание Faucet...';
            document.getElementById('txStatusText').style.color = '#f39c12';
            document.getElementById('txStatusLink').innerHTML = '<span style="color: #888;">Формирование хэша...</span>';
            document.getElementById('txStatusModal').style.display = 'flex';

            window.waitingForWalletTx = walletId;
            fetchAndUpdateTxs(walletId);
        } else {
            const data = await res.json();
            showGlobalAlert(`Ошибка: ${data.detail}`, true);
        }
    } catch (e) {
        showGlobalAlert('Сбой сети или сервер не отвечает при запросе Faucet', true);
    }
};

window.openTxHistory = (walletId, address) => {
    currentOpenWalletId = walletId;
    document.getElementById('txHistoryTitle').innerHTML = `Список транзакций <b>ETH</b> кошелька <b>${address}</b>`;
    const tbody = document.getElementById('txTableBody');
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">Загрузка...</td></tr>';
    document.getElementById('txHistoryModal').style.display = 'flex';
    fetchAndUpdateTxs(walletId);
};

// =====================================
// ЛОГИКА СОРТИРОВКИ ПО НАЖАТИЮ
// =====================================
window.toggleSort = function(col) {
    if (currentSortCol === col) {
        currentSortAsc = !currentSortAsc;
    } else {
        currentSortCol = col;
        currentSortAsc = false; // При выборе новой колонки всегда сначала сортируем от большего к меньшему (DESC)
    }
    applySortAndRender();
};

function applySortAndRender() {
    const columns = ['age', 'fee', 'status'];
    columns.forEach(c => {
        const el = document.getElementById(`sort-${c}`);
        if (el) el.innerHTML = '&#8597;'; // Иконка по умолчанию (вверх-вниз)
    });

    const icon = currentSortAsc ? '▲' : '▼';
    const activeEl = document.getElementById(`sort-${currentSortCol}`);
    if (activeEl) activeEl.textContent = icon;

    let sorted = [...currentModalTxs];
    sorted.sort((a, b) => {
        let valA, valB;

        if (currentSortCol === 'age') {
            valA = parseInt(a.timeStamp || 0);
            valB = parseInt(b.timeStamp || 0);
        } else if (currentSortCol === 'fee') {
            valA = getTxFee(a);
            valB = getTxFee(b);
        } else if (currentSortCol === 'status') {
            valA = getStatusVal(a);
            valB = getStatusVal(b);
        }

        if (valA < valB) return currentSortAsc ? -1 : 1;
        if (valA > valB) return currentSortAsc ? 1 : -1;
        return 0;
    });

    renderTxsTable(sorted);
}

function fetchAndUpdateTxs(walletId) {
    if (currentOpenWalletId !== walletId) return;

    if (!walletSocket || !walletSocket.connected) {
        document.getElementById('txTableBody').innerHTML = '<tr><td colspan="7" style="text-align:center; color:red;">Ошибка: нет подключения к серверу реального времени.</td></tr>';
        return;
    }

    walletSocket.emit("get_tx_history", { wallet_id: walletId }, (response) => {
        if (!response || response.status === "error") {
            document.getElementById('txTableBody').innerHTML = `<tr><td colspan="7" style="text-align:center; color:red;">Ошибка загрузки истории</td></tr>`;
            return;
        }
        currentModalTxs = response.data;
        applySortAndRender();
    });
}

function renderTxsTable(txs) {
    const tbody = document.getElementById('txTableBody');
    if (txs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">Транзакций не найдено.</td></tr>';
        return;
    }

    let newHtml = '';
    const seenHashes = new Set();

    txs.forEach((tx) => {
        const txHash = tx.hash || tx.tx_hash || tx.id;
        const safeHashId = txHash.toLowerCase();

        // Защита от дублей
        if (seenHashes.has(safeHashId) && safeHashId.startsWith('0x')) return;
        seenHashes.add(safeHashId);

        // Определение статуса
        const rawStatus = String(tx.status || "").toLowerCase();
        const isError = tx.isError === "1" || tx.txreceipt_status === "0" || rawStatus === "failed" || rawStatus === "error";
        const isSuccess = tx.txreceipt_status === "1" || rawStatus === "success" || (tx.blockNumber && parseInt(tx.blockNumber) > 0 && !isError);

        // Цвета как на скриншоте
        let statusHtml = '<span style="color: #fbc02d; font-size: 15px;">Pending</span>'; // Оранжевый
        let statusCode = 'pending';
        if (isSuccess) {
            statusHtml = '<span style="color: #4caf50; font-size: 15px;">Success</span>'; // Зеленый
            statusCode = 'success';
        } else if (isError) {
            statusHtml = '<span style="color: #f44336; font-size: 15px;">Failed</span>'; // Красный
            statusCode = 'failed';
        }

        // Форматирование суммы
        let valNum = parseFloat(tx.value || 0);
        if (valNum > 1000000000) valNum = valNum / 1e18;
        const valEth = Number(valNum.toFixed(15)).toString();

        const formatAddr = (addr) => {
            if (!addr || addr === '---') return '---';
            return addr.substring(0, 22) + '...';
        };

        const fromAddr = tx.from || tx.from_address || '---';
        const toAddr = tx.to || tx.to_address || '---';

        const fromDisplay = fromAddr !== '---' ? `<a href="https://sepolia.etherscan.io/address/${fromAddr}" target="_blank" class="tx-link" title="${fromAddr}">${formatAddr(fromAddr)}</a>` : '---';
        const toDisplay = toAddr !== '---' ? `<a href="https://sepolia.etherscan.io/address/${toAddr}" target="_blank" class="tx-link" title="${toAddr}">${formatAddr(toAddr)}</a>` : '---';

        let hashDisplay;
        if (txHash.startsWith('0x')) {
            hashDisplay = `<a href="https://sepolia.etherscan.io/tx/${txHash}" target="_blank" class="tx-link" title="Посмотреть в Etherscan">${formatAddr(txHash)}</a>`;
        } else {
            hashDisplay = `<span style="color: #888; font-family: monospace;">Pending...</span>`;
        }

        // Комиссия (Fee)
        const rawFee = getTxFee(tx);
        const txFeeHtml = rawFee > 0 ? `${Number(rawFee.toFixed(8)).toString()} <span style="color: #4caf50; font-size: 12px;" title="Txn Fee">💡</span>` : `0 <span style="color: #4caf50; font-size: 12px;">💡</span>`;

        const ageStr = timeAgo(tx.timeStamp);

        newHtml += `
            <tr id="tx-row-${safeHashId}">
                <td>${hashDisplay}</td>
                <td>${fromDisplay}</td>
                <td>${toDisplay}</td>
                <td><span style="color:#000;">${valEth} Ether</span></td>
                <td style="color: #3498db;">${ageStr}</td>
                <td style="color: #888;">${txFeeHtml}</td>
                <td style="text-align: center;">${statusHtml}</td>
            </tr>
        `;
    });

    tbody.innerHTML = newHtml;
}

window.closeModal = (id) => {
    document.getElementById(id).style.display = 'none';
    if (id === 'txHistoryModal') {
        currentOpenWalletId = null;
    }
};

function showGlobalAlert(message, isError = false, isWarning = false) {
    const alertDiv = document.getElementById('globalAlert');
    if (!alertDiv) { alert(message); return; }
    alertDiv.style.display = 'block';

    if (isWarning) {
        alertDiv.style.backgroundColor = '#fff3cd';
        alertDiv.style.color = '#856404';
        alertDiv.style.border = '1px solid #ffeeba';
    } else {
        alertDiv.style.backgroundColor = isError ? '#f8d7da' : '#d4edda';
        alertDiv.style.color = isError ? '#721c24' : '#155724';
        alertDiv.style.border = isError ? '1px solid #f5c6cb' : '1px solid #c3e6cb';
    }

    alertDiv.style.padding = '10px';
    alertDiv.style.borderRadius = '5px';
    alertDiv.style.marginBottom = '15px';
    alertDiv.textContent = message;

    setTimeout(() => { alertDiv.style.display = 'none'; }, 7000);
}

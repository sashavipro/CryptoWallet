let currentWallets =[];
let currentOpenWalletId = null;
let walletSocket = null;
window.waitingForWalletTx = null;

// Глобальные переменные для сортировки
let currentModalTxs =[];
let currentSortCol = 'age';
let currentSortAsc = false; // По умолчанию от новых к старым

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
    if (seconds < 60) return `${Math.max(0, seconds)} secs ago`;
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
    return 1; // Pending
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

            const responseData = await res.json();

            if (res.ok) {
                document.getElementById('sendToAddress').value = '';
                document.getElementById('sendValue').value = '';
                closeModal('sendTxModal');

                txChannel.postMessage({ type: 'NEW_PENDING_TX', walletId: walletId });

                document.getElementById('txStatusIcon').textContent = '⏳';
                document.getElementById('txStatusText').textContent = 'Ожидание сети...';
                document.getElementById('txStatusText').style.color = '#f39c12';
                document.getElementById('txStatusLink').innerHTML = '<span style="color: #888;">Формирование хэша...</span>';
                document.getElementById('txStatusModal').style.display = 'flex';

                window.waitingForWalletTx = walletId;
                fetchAndUpdateTxs(walletId);
            } else {
                let errorMsg = responseData.detail ? (Array.isArray(responseData.detail) ? responseData.detail[0].msg : responseData.detail) : "Неизвестная ошибка";
                resultDiv.innerHTML = `<span style="color: #e74c3c;">Ошибка: ${errorMsg}</span>`;
            }
        } catch (e) {
            resultDiv.innerHTML = `<span style="color: #e74c3c;">Ошибка сети.</span>`;
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

    walletSocket.on("connect", () => {
        console.log("Успешно подключились к WS /transaction!");
    });

    walletSocket.on("transaction_status_changed", (data) => {
        // Мгновенное обновление таблицы, если модалка открыта
        if (currentOpenWalletId && String(currentOpenWalletId) === String(data.wallet_id)) {
            fetchAndUpdateTxs(currentOpenWalletId);
        }

        const status = String(data.status || "").toLowerCase();
        const hashDisplay = data.tx_hash ? data.tx_hash.substring(0, 10) : '...';

        if (window.waitingForWalletTx && String(window.waitingForWalletTx) === String(data.wallet_id)) {
            const linkDiv = document.getElementById('txStatusLink');
            const textDiv = document.getElementById('txStatusText');
            const iconDiv = document.getElementById('txStatusIcon');

            if (data.tx_hash && data.tx_hash.startsWith('0x')) {
                linkDiv.innerHTML = `<a href="https://sepolia.etherscan.io/tx/${data.tx_hash}" target="_blank" style="color: #3498db; text-decoration: none; font-weight: bold;">Посмотреть транзакцию в Etherscan ↗</a>`;
            }

            if (status === 'success' || status === '1') {
                iconDiv.textContent = '✅';
                textDiv.textContent = 'Транзакция успешно завершена!';
                textDiv.style.color = '#27ae60';
                window.waitingForWalletTx = null;
            } else if (status === 'failed' || status === '0') {
                iconDiv.textContent = '❌';
                textDiv.textContent = 'Ошибка транзакции';
                textDiv.style.color = '#e74c3c';
                window.waitingForWalletTx = null;
            } else if (status === 'pending') {
                iconDiv.textContent = '⏳';
                textDiv.textContent = 'Отправлена в блокчейн...';
                textDiv.style.color = '#f39c12';
            }
        }

        // Показываем уведомление
        if (status === 'success' || status === '1') {
            showGlobalAlert(`Транзакция ${hashDisplay} успешно завершена!`);
        } else if (status === 'failed' || status === '0') {
            showGlobalAlert(`Транзакция ${hashDisplay} завершилась ошибкой`, true);
        } else if (status === 'pending') {
            showGlobalAlert(`Транзакция в обработке... Ожидаем блокчейн.`);
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
            txChannel.postMessage({ type: 'NEW_PENDING_TX', walletId: walletId });

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
// ЛОГИКА СОРТИРОВКИ В JS
// =====================================
window.toggleSort = function(col) {
    if (currentSortCol === col) {
        currentSortAsc = !currentSortAsc;
    } else {
        currentSortCol = col;
        currentSortAsc = (col === 'age') ? false : true;
    }
    applySortAndRender();
};

function applySortAndRender() {
    const cols =['age', 'fee', 'status'];
    cols.forEach(c => {
        const el = document.getElementById(`sort-${c}`);
        if (el) el.innerHTML = '&#8597;';
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
    if (!walletSocket || !walletSocket.connected) {
        document.getElementById('txTableBody').innerHTML = '<tr><td colspan="7" style="text-align:center; color:red;">Ошибка: нет подключения к серверу реального времени.</td></tr>';
        return;
    }

    walletSocket.emit("get_tx_history", { wallet_id: walletId }, (response) => {
        // Защита: пока ждали ответ, пользователь мог закрыть или переключить модалку
        if (currentOpenWalletId !== walletId) return;

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

    const myWallet = currentWallets.find(w => w.id === currentOpenWalletId);
    const myAddress = myWallet ? myWallet.address.toLowerCase() : '';

    let newHtml = '';
    const seenHashes = new Set();

    txs.forEach((tx) => {
        const txHash = tx.hash || tx.tx_hash || tx.id;
        const safeHashId = txHash.toLowerCase();

        if (seenHashes.has(safeHashId) && safeHashId.startsWith('0x')) return;
        seenHashes.add(safeHashId);

        const rawStatus = String(tx.status || "").toLowerCase();
        const isError = tx.isError === "1" || tx.txreceipt_status === "0" || rawStatus === "failed" || rawStatus === "error";
        const isSuccess = tx.txreceipt_status === "1" || rawStatus === "success" || (tx.blockNumber && parseInt(tx.blockNumber) > 0 && !isError);

        let statusHtml = '<span style="color: #f39c12; font-size: 14px; font-weight: bold;">Pending</span>';
        let statusCode = 'pending';
        if (isSuccess) {
            statusHtml = '<span style="color: #27ae60; font-size: 14px; font-weight: bold;">Success</span>';
            statusCode = 'success';
        } else if (isError) {
            statusHtml = '<span style="color: #e74c3c; font-size: 14px; font-weight: bold;">Failed</span>';
            statusCode = 'failed';
        }

        let valNum = parseFloat(tx.value || 0);
        if (valNum > 1000000000) valNum = valNum / 1e18;
        const valEth = Number(valNum.toFixed(15)).toString();

        const formatAddr = (addr) => {
            if (!addr || addr === '---') return '---';
            return addr.substring(0, 18) + '...';
        };

        const fromAddr = tx.from || tx.from_address || '---';
        const toAddr = tx.to || tx.to_address || '---';

        const isOut = fromAddr.toLowerCase() === myAddress;
        const typeBadge = `<span class="${isOut ? 'badge-out' : 'badge-in'}">${isOut ? 'OUT' : 'IN'}</span>`;

        const fromDisplay = fromAddr !== '---' ? `<a href="https://sepolia.etherscan.io/address/${fromAddr}" target="_blank" class="tx-link" title="${fromAddr}">${formatAddr(fromAddr)}</a>` : '---';
        const toDisplay = toAddr !== '---' ? `<a href="https://sepolia.etherscan.io/address/${toAddr}" target="_blank" class="tx-link" title="${toAddr}">${formatAddr(toAddr)}</a>` : '---';

        let hashDisplay;
        if (txHash.startsWith('0x')) {
            hashDisplay = `<a href="https://sepolia.etherscan.io/tx/${txHash}" target="_blank" class="tx-link" title="Посмотреть в Etherscan">${formatAddr(txHash)}</a>`;
        } else {
            hashDisplay = `<span style="color: #888; font-family: monospace;">Pending...</span>`;
        }

        const rawFee = getTxFee(tx);
        const txFee = rawFee > 0 ? Number(rawFee.toFixed(8)).toString() : '0';
        const ageStr = timeAgo(tx.timeStamp);

        newHtml += `
            <tr id="tx-row-${safeHashId}">
                <td>${hashDisplay}</td>
                <td>${fromDisplay}</td>
                <td>${toDisplay}</td>
                <td><strong>${valEth}</strong> Ether</td>
                <td style="color: #3498db;">${ageStr}</td>
                <td style="text-align: right; color: #555;">${txFee}</td>
                <td id="tx-status-${safeHashId}" data-status="${statusCode}" style="text-align: center;">${statusHtml}</td>
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
    if (!alertDiv) {
        alert(message);
        return;
    }
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

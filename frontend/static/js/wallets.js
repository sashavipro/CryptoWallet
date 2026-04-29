// Глобальные переменные
let currentWallets =[];
let currentOpenWalletId = null;
let walletSocket = null;
window.waitingForWalletTx = null;

function getCookie(name) {
    let matches = document.cookie.match(new RegExp(
        "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
    ));
    return matches ? decodeURIComponent(matches[1]) : undefined;
}

// Формат возраста в стиле Etherscan
function timeAgo(timestampSeconds) {
    if (!timestampSeconds) return '---';
    const seconds = Math.floor(Date.now() / 1000) - parseInt(timestampSeconds);
    if (seconds < 60) return `${Math.max(0, seconds)} secs ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} mins ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hrs ago`;
    const days = Math.floor(hours / 24);
    return `${days} days ago`;
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
                headers: { 'Content-Type': 'application/json' },
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

                txChannel.postMessage({
                    type: 'NEW_PENDING_TX',
                    walletId: walletId
                });

                document.getElementById('txStatusIcon').textContent = '⏳';
                document.getElementById('txStatusText').textContent = 'Ожидание сети...';
                document.getElementById('txStatusText').style.color = '#f39c12';
                document.getElementById('txStatusLink').innerHTML = '<span style="color: #888;">Формирование хэша...</span>';
                document.getElementById('txStatusModal').style.display = 'flex';

                window.waitingForWalletTx = walletId;
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

function initWalletSocket() {
    if (typeof io === 'undefined') {
        console.error("Ошибка: Библиотека Socket.IO не загружена!");
        return;
    }

    const token = getCookie('access_token');
    if (!token) return;

    walletSocket = io("/transaction", {
        auth: { token: token },
        transports: ['websocket']
    });

    walletSocket.on("connect", () => {
        console.log("Успешно подключились к WS /transaction!");
    });

    walletSocket.on("connect_error", (err) => {
        console.error("Ошибка WS /transaction:", err.message);
    });

    walletSocket.on("transaction_status_changed", (data) => {
        if (currentOpenWalletId && (String(currentOpenWalletId) === String(data.wallet_id) || !data.wallet_id)) {
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

        if (status === 'success' || status === '1') {
            showGlobalAlert(`Транзакция ${hashDisplay} успешно завершена!`);
        } else if (status === 'failed' || status === '0') {
            const errorReason = data.error ? `: ${data.error}` : '';
            showGlobalAlert(`Транзакция ${hashDisplay} завершилась ошибкой${errorReason}`, true);
        } else if (status === 'pending') {
            showGlobalAlert(`Транзакция отправлена в сеть. Ожидаем майнинга...`, false, true);
        }
    });

    walletSocket.on("balance_updated", (data) => {
        const balanceSpan = document.getElementById(`balance-${data.wallet_id}`);
        if (balanceSpan) {
            const newText = parseFloat(data.balance).toFixed(4);
            if (balanceSpan.textContent !== newText) {
                balanceSpan.style.color = '#27ae60';
                balanceSpan.style.fontWeight = 'bold';
                setTimeout(() => {
                    balanceSpan.style.color = '';
                    balanceSpan.style.fontWeight = '';
                }, 2000);
                balanceSpan.textContent = newText;
            }
        }
    });
}

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
        const res = await fetch(`/api/v1/faucet/${walletId}/request-eth`, { method: 'POST' });
        const contentType = res.headers.get("content-type");
        let data = null;
        if (contentType && contentType.includes("application/json")) {
            data = await res.json();
        }

        if (res.ok) {
            showGlobalAlert('ETH успешно запрошен! Ожидайте подтверждения сети.');
            txChannel.postMessage({ type: 'NEW_PENDING_TX', walletId: walletId });

            document.getElementById('txStatusIcon').textContent = '⏳';
            document.getElementById('txStatusText').textContent = 'Ожидание Faucet...';
            document.getElementById('txStatusText').style.color = '#f39c12';
            document.getElementById('txStatusLink').innerHTML = '<span style="color: #888;">Формирование хэша...</span>';
            document.getElementById('txStatusModal').style.display = 'flex';
            window.waitingForWalletTx = walletId;

        } else {
            let errorMsg = data && data.detail ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)) : `Ошибка сервера (Код ${res.status})`;

            if (errorMsg.includes('через') || errorMsg.includes('доступен')) {
                showGlobalAlert(` ${errorMsg}`, false, true);
            } else {
                showGlobalAlert(`Ошибка Faucet: ${errorMsg}`, true);
            }
        }
    } catch (e) {
        showGlobalAlert('Сбой сети или сервер не отвечает при запросе Faucet', true);
    }
};

window.openTxHistory = (walletId, address) => {
    currentOpenWalletId = walletId;
    // Обновляем заголовок как в макете
    document.getElementById('txHistoryTitle').innerHTML = `Список транзакций <b>ETH</b> кошелька <b>${address}</b>`;
    const tbody = document.getElementById('txTableBody');

    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">Загрузка...</td></tr>';
    document.getElementById('txHistoryModal').style.display = 'flex';

    fetchAndUpdateTxs(walletId);
};

function fetchAndUpdateTxs(walletId) {
    if (currentOpenWalletId !== walletId) return;
    const tbody = document.getElementById('txTableBody');

    if (!walletSocket || !walletSocket.connected) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:red;">Ошибка: нет подключения к серверу реального времени.</td></tr>';
        return;
    }

    walletSocket.emit("get_tx_history", { wallet_id: walletId }, (response) => {
        if (!response || response.status === "error") {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:red;">Ошибка загрузки истории: ${response?.message || 'Неизвестная ошибка'}</td></tr>`;
            return;
        }

        const txs = response.data;

        if (txs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">Транзакций не найдено.</td></tr>';
            return;
        }

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

            // Стили статуса точно по макету
            let statusHtml = '<span style="color: #f39c12; font-size: 15px;">Pending</span>';
            let statusCode = 'pending';
            if (isSuccess) {
                statusHtml = '<span style="color: #27ae60; font-size: 15px;">Success</span>';
                statusCode = 'success';
            } else if (isError) {
                statusHtml = '<span style="color: #e74c3c; font-size: 15px;">Failed</span>';
                statusCode = 'failed';
            }

            // Сумма (убираем лишние нули)
            let valNum = parseFloat(tx.value || 0);
            if (valNum > 1000000000) valNum = valNum / 1e18;
            const valEth = Number(valNum.toFixed(15)).toString();

            // Функция обрезки адресов для ссылок
            const formatAddr = (addr) => {
                if (!addr || addr === '---') return '---';
                return addr.substring(0, 18) + '...';
            };

            const fromAddr = tx.from || tx.from_address || '---';
            const toAddr = tx.to || tx.to_address || '---';

            const fromDisplay = fromAddr !== '---' ? `<a href="https://sepolia.etherscan.io/address/${fromAddr}" target="_blank" class="tx-link" title="${fromAddr}">${formatAddr(fromAddr)}</a>` : '---';
            const toDisplay = toAddr !== '---' ? `<a href="https://sepolia.etherscan.io/address/${toAddr}" target="_blank" class="tx-link" title="${toAddr}">${formatAddr(toAddr)}</a>` : '---';

            let hashDisplay;
            if (txHash.startsWith('0x')) {
                hashDisplay = `<a href="https://sepolia.etherscan.io/tx/${txHash}" target="_blank" class="tx-link" title="Посмотреть в Etherscan">${formatAddr(txHash)}</a>`;
            } else {
                hashDisplay = `<span style="color: #888;" title="Ожидание формирования хэша сети">Ожидание...</span>`;
            }

            // Комиссия и лампочка
            const txFee = tx.tx_fee ? Number(parseFloat(tx.tx_fee).toFixed(8)).toString() : '0';
            const ageStr = timeAgo(tx.timeStamp);

            // HTML строки
            newHtml += `
                <tr id="tx-row-${safeHashId}">
                    <td>${hashDisplay}</td>
                    <td>${fromDisplay}</td>
                    <td>${toDisplay}</td>
                    <td>${valEth} Ether</td>
                    <td style="color: #3498db;">${ageStr}</td>
                    <td>${txFee} <span style="color: #27ae60; font-size: 12px;" title="Txn Fee">💡</span></td>
                    <td id="tx-status-${safeHashId}" data-status="${statusCode}" style="text-align: center;">${statusHtml}</td>
                </tr>
            `;
        });

        tbody.innerHTML = newHtml;
    });
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

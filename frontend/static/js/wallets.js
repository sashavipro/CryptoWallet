// Глобальная переменная для хранения кошельков
let currentWallets = [];

document.addEventListener('DOMContentLoaded', () => {
    loadWallets();

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
                    <span style="color: #27ae60; font-weight: bold;">Отправка произведена.</span><br>
                    <a href="https://sepolia.etherscan.io/tx/${data.tx_hash}" target="_blank" style="color: #3498db;">Ссылка на транзакцию</a>
                `;
                document.getElementById('sendToAddress').value = '';
                document.getElementById('sendValue').value = '';
                setTimeout(loadWallets, 30000);
            } else {
                // 422 ошибки от FastAPI
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
                // ИСПРАВЛЕНИЕ 1: Оставляем спан "Загрузка..." для баланса
                card.innerHTML = `
                    <div class="wallet-header">
                        <div style="font-size: 30px; color: #627eea;">⟠</div>
                        <div class="wallet-info">
                            <div class="wallet-label">Адрес:</div>
                            <a href="https://sepolia.etherscan.io/address/${wallet.address}" target="_blank" class="wallet-address">${wallet.address}</a>
                            <div class="wallet-balance"><span id="balance-${wallet.id}">Загрузка...</span> ETH</div>
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

            // Асинхронно запрашиваем реальный баланс для каждого кошелька
            currentWallets.forEach(async (wallet) => {
                try {
                    const balRes = await fetch(`/api/v1/wallets/${wallet.id}/balance`);
                    if (balRes.ok) {
                        const balData = await balRes.json();
                        document.getElementById(`balance-${wallet.id}`).textContent = parseFloat(balData.balance).toFixed(4);
                    } else {
                        document.getElementById(`balance-${wallet.id}`).textContent = "Ошибка";
                    }
                } catch (e) {
                    document.getElementById(`balance-${wallet.id}`).textContent = "Ошибка";
                }
            });
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
    showGlobalAlert('Запрос отправлен в Faucet. Ожидайте...', false);
    try {
        const res = await fetch(`/api/v1/faucet/${walletId}/request-eth`, { method: 'POST' });

        // Проверяем, вернул ли сервер JSON, чтобы не было ошибки парсинга при 500 ошибках
        const contentType = res.headers.get("content-type");
        let data = null;
        if (contentType && contentType.includes("application/json")) {
            data = await res.json();
        }

        if (res.ok) {
            showGlobalAlert('ETH успешно запрошен! Баланс скоро обновится.');
            setTimeout(loadWallets, 5000);
        } else {
            let errorMsg = data && data.detail ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)) : `Ошибка сервера (Код ${res.status})`;
            showGlobalAlert(`Ошибка Faucet: ${errorMsg}`, true);
        }
    } catch (e) {
        console.error("Ошибка Faucet:", e);
        showGlobalAlert('Сбой сети или сервер не отвечает при запросе Faucet', true);
    }
};

// Открытие модалки истории
window.openTxHistory = async (walletId, address) => {
    document.getElementById('txHistoryTitle').textContent = `Список транзакций ${address.substring(0,8)}...`;
    const tbody = document.getElementById('txTableBody');
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">Загрузка...</td></tr>';
    document.getElementById('txHistoryModal').style.display = 'flex';

    try {
        const res = await fetch(`/api/v1/transactions/wallet/${walletId}`);
        if (res.ok) {
            const txs = await res.json();
            tbody.innerHTML = '';

            if (txs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">Транзакций нет.</td></tr>';
                return;
            }

            txs.forEach(tx => {
                const isError = tx.isError === "1" || tx.status === "failed";
                const isPending = tx.status === "pending";

                let statusHtml = '<span class="status-success" style="color: #27ae60; font-weight: bold;">Success</span>';
                if (isError) statusHtml = '<span class="status-failed" style="color: #e74c3c; font-weight: bold;">Failed</span>';
                if (isPending) statusHtml = '<span class="status-pending" style="color: #f39c12; font-weight: bold;">Pending</span>';

                let valEth = tx.value;
                if (valEth && valEth.length > 10) {
                    valEth = (parseFloat(valEth) / 1e18).toFixed(4);
                }

                tbody.innerHTML += `
                    <tr>
                        <td><a href="https://sepolia.etherscan.io/tx/${tx.hash || tx.tx_hash}" target="_blank" class="tx-hash" style="color: #3498db; text-decoration: none;">${(tx.hash || tx.tx_hash).substring(0, 10)}...</a></td>
                        <td class="tx-addr">${(tx.from || tx.from_address).substring(0, 10)}...</td>
                        <td class="tx-addr">${(tx.to || tx.to_address).substring(0, 10)}...</td>
                        <td>${valEth} ETH</td>
                        <td>${tx.gasUsed ? (tx.gasUsed * tx.gasPrice / 1e18).toFixed(6) : (tx.tx_fee || '0')}</td>
                        <td>${statusHtml}</td>
                    </tr>
                `;
            });
        }
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:red;">Ошибка загрузки.</td></tr>';
    }
};

window.closeModal = (id) => {
    document.getElementById(id).style.display = 'none';
};

// Функция для вывода уведомлений
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

    setTimeout(() => { alertDiv.style.display = 'none'; }, 5000);
}

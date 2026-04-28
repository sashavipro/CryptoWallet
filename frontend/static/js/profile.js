document.addEventListener('DOMContentLoaded', () => {
    // Элементы профиля
    const btnSaveProfile = document.getElementById('btnSaveProfile');
    const inputUsername = document.getElementById('username');
    const inputEmail = document.getElementById('email');
    const inputOldPassword = document.getElementById('oldPassword');
    const inputNewPassword = document.getElementById('newPassword');
    const inputRepeatPassword = document.getElementById('repeatPassword');
    const profileAlert = document.getElementById('profileAlert');
    const profileHeaderName = document.getElementById('profileHeaderName');

    // Элементы аватара
    const btnRemoveAvatar = document.getElementById('btnRemoveAvatar');
    const btnUpdateAvatar = document.getElementById('btnUpdateAvatar');
    const avatarUploadInput = document.getElementById('avatarUploadInput');
    const profileAvatar = document.getElementById('profileAvatar');

    // Элементы кошельков и статистики
    const importWalletModal = document.getElementById('importWalletModal');
    const btnOpenImportModal = document.getElementById('btnOpenImportModal');
    const btnCloseImportModal = document.getElementById('btnCloseImportModal');
    const btnCreateWallet = document.getElementById('btnCreateWallet');
    const btnSaveWallet = document.getElementById('btnSaveWallet');
    const privateKeyInput = document.getElementById('privateKeyInput');
    const walletsList = document.getElementById('walletsList');
    const statWallets = document.getElementById('statWallets');
    const statMessages = document.getElementById('statMessages');

    let initialUsername = '';
    let ethAssetId = null;

    // ==========================================
    // БЕЗОПАСНОЕ ИЗВЛЕЧЕНИЕ ТОКЕНА
    // ==========================================
    function getToken() {
        let token = null;
        const value = `; ${document.cookie}`;
        const parts = value.split(`; access_token=`);

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

    const checkUnauthorized = (res) => {
        if (res.status === 401 || res.status === 403) {
            alert("Ваша сессия истекла. Пожалуйста, авторизуйтесь заново.");
            document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            window.location.href = "/login";
            return true;
        }
        return false;
    };

    function showAlert(message, isError = false) {
        profileAlert.style.display = 'block';
        profileAlert.style.backgroundColor = isError ? '#f8d7da' : '#d4edda';
        profileAlert.style.color = isError ? '#721c24' : '#155724';
        profileAlert.style.border = `1px solid ${isError ? '#f5c6cb' : '#c3e6cb'}`;
        profileAlert.textContent = message;

        setTimeout(() => { profileAlert.style.display = 'none'; }, 5000);
    }

    // Слушаем событие от main.js
    document.addEventListener('UserDataLoaded', () => {
        const user = window.currentUser;
        if (!user) return;

        inputUsername.value = user.username;
        inputEmail.value = user.email;
        initialUsername = user.username;

        if (profileHeaderName) {
            profileHeaderName.textContent = user.username;
        }

        if (user.avatar_url && !user.avatar_url.startsWith('data:image')) {
            profileAvatar.src = user.avatar_url;
        }
    });

    // ==========================================
    // 1. ОБРАБОТКА ПРОФИЛЯ (ИМЯ И ПАРОЛЬ)
    // ==========================================
    btnSaveProfile.addEventListener('click', async () => {
        let hasChanges = false;
        const token = getToken();

        // Обновление Username
        const newUsername = inputUsername.value.trim();
        if (newUsername !== initialUsername) {
            hasChanges = true;
            try {
                const res = await fetch('/api/v1/profile/me', {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ username: newUsername })
                });

                if (checkUnauthorized(res)) return;

                if (!res.ok) {
                    const data = await res.json();
                    showAlert(`Ошибка обновления имени: ${data.detail}`, true);
                    return;
                }
                initialUsername = newUsername;
            } catch (e) {
                showAlert('Сетевая ошибка при обновлении профиля', true);
                return;
            }
        }

        // Смена пароля
        const oldPass = inputOldPassword.value;
        const newPass = inputNewPassword.value;
        const repeatPass = inputRepeatPassword.value;

        if (oldPass || newPass || repeatPass) {
            hasChanges = true;
            if (newPass !== repeatPass) {
                showAlert('Новые пароли не совпадают!', true);
                return;
            }
            if (!oldPass) {
                showAlert('Введите текущий пароль для подтверждения изменений', true);
                return;
            }

            try {
                const res = await fetch('/api/v1/profile/password', {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ old_password: oldPass, new_password: newPass })
                });

                if (checkUnauthorized(res)) return;

                if (!res.ok) {
                    const data = await res.json();
                    showAlert(`Ошибка смены пароля: ${data.detail}`, true);
                    return;
                }

                inputOldPassword.value = '';
                inputNewPassword.value = '';
                inputRepeatPassword.value = '';
            } catch (e) {
                showAlert('Сетевая ошибка при смене пароля', true);
                return;
            }
        }

        if (hasChanges) {
            showAlert('Профиль успешно обновлен!');
            document.querySelector('.header .username').textContent = newUsername;
            if (profileHeaderName) profileHeaderName.textContent = newUsername;
        } else {
            showAlert('Нет изменений для сохранения.');
        }
    });

    // ==========================================
    // 2. ОБРАБОТКА АВАТАРОВ (РЕАЛЬНАЯ ЗАГРУЗКА В S3)
    // ==========================================
    btnRemoveAvatar.addEventListener('click', async () => {
        if (!confirm('Вы уверены, что хотите удалить аватарку?')) return;

        try {
            const res = await fetch('/api/v1/profile/me/avatar', {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${getToken()}` }
            });

            if (checkUnauthorized(res)) return;

            if (res.ok) {
                profileAvatar.src = '/static/img/default-avatar.png';
                document.getElementById('navAvatar').src = '/static/img/default-avatar.png';
                if (window.currentUser) window.currentUser.avatar_url = null;
                showAlert('Аватар успешно удален');
            } else {
                showAlert('Ошибка при удалении аватара', true);
            }
        } catch (e) {
            console.error(e);
            showAlert('Ошибка сети при удалении аватара', true);
        }
    });

    btnUpdateAvatar.addEventListener('click', () => {
        avatarUploadInput.click();
    });

    avatarUploadInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        try {
            showAlert('Получение ссылки для загрузки...', false);

            const extension = file.name.split('.').pop();
            const contentType = file.type;

            // 1. Получаем Presigned URL от бэкенда
            const urlRes = await fetch(`/api/v1/profile/me/avatar/presigned-url?extension=${extension}&content_type=${encodeURIComponent(contentType)}`, {
                headers: { 'Authorization': `Bearer ${getToken()}` }
            });

            if (checkUnauthorized(urlRes)) return;

            if (!urlRes.ok) {
                showAlert('Ошибка при генерации ссылки для загрузки', true);
                return;
            }

            const { upload_url, public_url } = await urlRes.json();

            showAlert('Загрузка картинки в облако (S3)...', false);

            // 2. Отправляем файл напрямую в DigitalOcean Spaces
            const s3Res = await fetch(upload_url, {
                method: 'PUT',
                headers: {
                    'Content-Type': contentType,
                    'x-amz-acl': 'public-read' // Делаем файл публичным
                },
                body: file
            });

            if (!s3Res.ok) {
                showAlert('Ошибка при загрузке картинки в S3', true);
                return;
            }

            showAlert('Сохранение ссылки в базу данных...', false);

            // 3. Сохраняем публичную ссылку в базу (PATCH /me)
            const updateRes = await fetch('/api/v1/profile/me', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getToken()}`
                },
                body: JSON.stringify({ avatar_url: public_url })
            });

            if (updateRes.ok) {
                profileAvatar.src = public_url;
                document.getElementById('navAvatar').src = public_url;
                if (window.currentUser) window.currentUser.avatar_url = public_url;
                showAlert('Аватар успешно обновлен и сохранен!');
            } else {
                showAlert('Ошибка при сохранении ссылки в профиль', true);
            }

        } catch (error) {
            console.error(error);
            showAlert('Сетевая ошибка при обновлении аватара', true);
        } finally {
            avatarUploadInput.value = ''; // Сбрасываем input
        }
    });

    // ==========================================
    // 3. УПРАВЛЕНИЕ КОШЕЛЬКАМИ И СТАТИСТИКА
    // ==========================================

    async function loadWallets() {
        try {
            const res = await fetch('/api/v1/wallets', {
                headers: { 'Authorization': `Bearer ${getToken()}` }
            });

            if (checkUnauthorized(res)) return;

            if (res.ok) {
                const wallets = await res.json();
                statWallets.textContent = wallets.length;

                walletsList.innerHTML = '';

                if (wallets.length === 0) {
                    walletsList.innerHTML = '<div style="color: #888; padding: 10px;">У вас пока нет кошельков. Создайте или импортируйте новый.</div>';
                    return;
                }

                wallets.forEach(wallet => {
                    walletsList.innerHTML += `
                        <div class="wallet-item" style="display: flex; align-items: center; width: 100%; gap: 10px;">
                            <span style="font-size: 18px; color: #3498db;">⟠</span>
                            <a href="https://sepolia.etherscan.io/address/${wallet.address}" target="_blank" style="font-size: 13px; text-decoration: none; color: #3498db; font-family: monospace; font-weight: bold;">
                                ${wallet.address}
                            </a>
                            <button class="btn-action" style="margin-left: auto; background-color: #e74c3c; padding: 5px 10px; font-size: 12px; border: none; border-radius: 4px; color: white; cursor: pointer;" onclick="deleteWallet('${wallet.id}')">Удалить</button>
                        </div>
                    `;
                });
            }
        } catch (e) {
            console.error("Ошибка загрузки кошельков:", e);
            walletsList.innerHTML = '<div style="color: red; padding: 10px;">Ошибка при загрузке кошельков.</div>';
        }
    }

    // Глобальная функция для удаления кошелька
    window.deleteWallet = async (walletId) => {
        if (!confirm('Вы уверены, что хотите удалить этот кошелек?')) return;

        try {
            const res = await fetch(`/api/v1/wallets/${walletId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${getToken()}` }
            });

            if (checkUnauthorized(res)) return;

            if (res.ok || res.status === 204) {
                showAlert('Кошелек успешно удален!');
                loadWallets();
            } else {
                const data = await res.json();
                showAlert(`Ошибка: ${data.detail || 'Не удалось удалить кошелек'}`, true);
            }
        } catch (e) {
            showAlert('Ошибка сети при удалении кошелька', true);
        }
    };

    // Получаем UUID актива (ETH)
    async function loadAssetId() {
        try {
            const res = await fetch('/api/v1/assets', {
                headers: { 'Authorization': `Bearer ${getToken()}` }
            });

            if (res.ok) {
                const assets = await res.json();
                const eth = assets.find(a => a.ticker === 'ETH');
                if (eth) {
                    ethAssetId = eth.id;
                }
            }
        } catch (e) {
            console.error("Ошибка сети (API assets):", e);
        }
    }

    // Создание нового кошелька
    btnCreateWallet.addEventListener('click', async () => {
        if (!ethAssetId) {
            showAlert('Системная ошибка: Актив ETH не загружен.', true);
            return;
        }

        btnCreateWallet.disabled = true;

        try {
            const res = await fetch(`/api/v1/wallets`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getToken()}`
                },
                body: JSON.stringify({ asset_id: ethAssetId })
            });

            if (checkUnauthorized(res)) return;

            if (res.ok) {
                showAlert('Новый ETH кошелек успешно создан!');
                loadWallets();
            } else {
                const data = await res.json();
                let errorMsg = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
                showAlert(`Ошибка: ${errorMsg}`, true);
            }
        } catch (e) {
            showAlert('Ошибка сети при создании кошелька', true);
        } finally {
            btnCreateWallet.disabled = false;
        }
    });

    // Импорт кошелька
    btnSaveWallet.addEventListener('click', async () => {
        const privateKey = privateKeyInput.value.trim();
        if (!privateKey) {
            showAlert('Введите приватный ключ!', true);
            return;
        }
        if (!ethAssetId) {
            showAlert('Системная ошибка: Актив ETH не загружен.', true);
            return;
        }

        btnSaveWallet.disabled = true;

        try {
            const res = await fetch('/api/v1/wallets/import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getToken()}`
                },
                body: JSON.stringify({
                    asset_id: ethAssetId,
                    private_key: privateKey
                })
            });

            if (checkUnauthorized(res)) return;

            if (res.ok) {
                showAlert('Кошелек успешно импортирован!');
                privateKeyInput.value = '';
                importWalletModal.style.display = 'none';
                loadWallets();
            } else {
                const data = await res.json();
                showAlert(`Ошибка импорта: ${data.detail || 'Неизвестная ошибка'}`, true);
            }
        } catch (e) {
            showAlert('Ошибка сети при импорте', true);
        } finally {
            btnSaveWallet.disabled = false;
        }
    });

    // Загрузка статистики
    async function loadStats() {
        try {
            const res = await fetch('/api/v1/profile/me/stats', {
                headers: { 'Authorization': `Bearer ${getToken()}` }
            });
            if (res.ok) {
                const stats = await res.json();
                if (stats.total_messages !== undefined) {
                    statMessages.textContent = stats.total_messages;
                }
            }
        } catch (e) {
            console.error("Ошибка загрузки статистики:", e);
        }
    }

    // Модальное окно кошельков (открытие/закрытие)
    btnOpenImportModal.addEventListener('click', () => {
        importWalletModal.style.display = 'flex';
    });
    btnCloseImportModal.addEventListener('click', () => {
        importWalletModal.style.display = 'none';
    });
    importWalletModal.addEventListener('click', (e) => {
        if (e.target === importWalletModal) {
            importWalletModal.style.display = 'none';
        }
    });

    // Инициализация
    loadAssetId().then(() => { loadWallets(); });
    loadStats();

    // Сокеты
    if (typeof io !== 'undefined') {
        const txSocket = io("/transaction", {
            auth: { token: getToken() },
            transports: ['websocket', 'polling']
        });

        txSocket.on("stats_updated", (data) => {
            if (data.messages_count !== undefined && statMessages) {
                statMessages.textContent = data.messages_count;
                statMessages.style.color = 'green';
                setTimeout(() => statMessages.style.color = '', 1000);
            }

            if (data.wallets_count !== undefined && statWallets) {
                statWallets.textContent = data.wallets_count;
                statWallets.style.color = 'green';
                setTimeout(() => statWallets.style.color = '', 1000);
            }
        });
    }
});

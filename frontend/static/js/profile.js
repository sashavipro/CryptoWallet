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
    const btnSaveWallet = document.getElementById('btnSaveWallet'); // Внутри модалки
    const privateKeyInput = document.getElementById('privateKeyInput');
    const walletsList = document.getElementById('walletsList');
    const statWallets = document.getElementById('statWallets');
    const statMessages = document.getElementById('statMessages');

    let initialUsername = '';
    let ethAssetId = null; // Будет хранить UUID актива ETH из БД

    // Вспомогательная функция для проверки на 401/403 ошибку
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

    // Слушаем событие от main.js, когда данные получены с бэкенда
    document.addEventListener('UserDataLoaded', () => {
        const user = window.currentUser;
        if (!user) return;

        inputUsername.value = user.username;
        inputEmail.value = user.email;
        initialUsername = user.username;

        if (profileHeaderName) {
            profileHeaderName.textContent = user.username;
        }

        if (user.avatar_url) {
            profileAvatar.src = user.avatar_url;
        }
    });

    // ==========================================
    // 1. ОБРАБОТКА ПРОФИЛЯ (ИМЯ И ПАРОЛЬ)
    // ==========================================
    btnSaveProfile.addEventListener('click', async () => {
        let hasChanges = false;

        // Обновление Username
        const newUsername = inputUsername.value.trim();
        if (newUsername !== initialUsername) {
            hasChanges = true;
            try {
                const res = await fetch('/api/v1/profile/me', {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
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
                    headers: { 'Content-Type': 'application/json' },
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
    // 2. ОБРАБОТКА АВАТАРОВ (S3)
    // ==========================================
    btnRemoveAvatar.addEventListener('click', async () => {
        if (!confirm('Вы уверены, что хотите удалить аватарку?')) return;

        try {
            const res = await fetch('/api/v1/profile/me/avatar', { method: 'DELETE' });
            if (res.ok) {
                profileAvatar.src = '/static/img/default-avatar.png';
                document.getElementById('navAvatar').src = '/static/img/default-avatar.png';
                showAlert('Аватар удален');
            } else {
                showAlert('Ошибка при удалении аватара', true);
            }
        } catch (e) {
            console.error(e);
        }
    });

    btnUpdateAvatar.addEventListener('click', () => {
        avatarUploadInput.click();
    });

    avatarUploadInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        try {
            const extension = file.name.split('.').pop();
            const urlRes = await fetch(`/api/v1/profile/me/avatar/presigned-url?extension=${extension}&content_type=${file.type}`);

            if (checkUnauthorized(urlRes)) return;

            if (!urlRes.ok) {
                showAlert('Ошибка при генерации ссылки для загрузки', true);
                return;
            }

            const { upload_url, public_url } = await urlRes.json();

            const s3Res = await fetch(upload_url, {
                method: 'PUT',
                headers: { 'Content-Type': file.type },
                body: file
            });

            if (!s3Res.ok) {
                showAlert('Ошибка при загрузке картинки в облако', true);
                return;
            }

            const updateRes = await fetch('/api/v1/profile/me', {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ avatar_url: public_url })
            });

            if (updateRes.ok) {
                profileAvatar.src = public_url;
                document.getElementById('navAvatar').src = public_url;
                showAlert('Аватар успешно обновлен!');
            } else {
                showAlert('Ошибка при сохранении ссылки в базу', true);
            }

        } catch (error) {
            console.error(error);
            showAlert('Сетевая ошибка при обновлении аватара', true);
        } finally {
            avatarUploadInput.value = '';
        }
    });

    // ==========================================
    // 3. УПРАВЛЕНИЕ КОШЕЛЬКАМИ И СТАТИСТИКА
    // ==========================================

    async function loadWallets() {
        try {
            const res = await fetch('/api/v1/wallets');

            if (checkUnauthorized(res)) return;

            if (res.ok) {
                const wallets = await res.json();
                statWallets.textContent = wallets.length;

                walletsList.innerHTML = ''; // Очищаем список

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
                method: 'DELETE'
            });

            if (checkUnauthorized(res)) return;

            if (res.ok) {
                showAlert('Кошелек успешно удален!');
                loadWallets(); // Перезагружаем список
            } else {
                const data = await res.json();
                showAlert(`Ошибка: ${data.detail || 'Не удалось удалить кошелек'}`, true);
            }
        } catch (e) {
            showAlert('Ошибка сети при удалении кошелька', true);
        }
    };

    // Получаем UUID актива (ETH) из бэкенда
    async function loadAssetId() {
        try {
            console.log("Отправляем запрос на /api/v1/assets...");
            const res = await fetch('/api/v1/assets');
            console.log("Статус ответа сервера:", res.status);

            if (res.ok) {
                const assets = await res.json();
                console.log("Данные, пришедшие с сервера:", assets);

                const eth = assets.find(a => a.ticker === 'ETH');
                if (eth) {
                    ethAssetId = eth.id;
                    console.log("ID актива ETH успешно найден и сохранен:", ethAssetId);
                } else {
                    console.error("Сервер вернул данные, но тикера 'ETH' там нет!");
                }
            } else {
                console.error("Ошибка API. Сервер ответил статусом:", res.status, await res.text());
            }
        } catch (e) {
            console.error("Ошибка сети (возможно, API недоступно или блочит CORS):", e);
        }
    }

    // Создание нового кошелька
    btnCreateWallet.addEventListener('click', async () => {
        if (!ethAssetId) {
            showAlert('Системная ошибка: Актив ETH не загружен.', true);
            return;
        }
        try {
            // Отправляем asset_id в теле запроса (body) в формате JSON
            const res = await fetch(`/api/v1/wallets`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    asset_id: ethAssetId
                })
            });

            if (checkUnauthorized(res)) return;

            if (res.ok) {
                showAlert('Новый ETH кошелек успешно создан!');
                loadWallets();
            } else {
                const data = await res.json();
                console.error("Ответ бэкенда с ошибкой:", data); // Вывод в консоль разработчика для дебага

                let errorMsg = "Неизвестная ошибка";
                if (data.detail) {
                    if (typeof data.detail === "string") {
                        errorMsg = data.detail; // Обычная текстовая ошибка
                    } else if (Array.isArray(data.detail)) {
                        errorMsg = data.detail[0].msg || JSON.stringify(data.detail); // Ошибка валидации 422
                    } else {
                        // Кастомный объект ошибки (например, уже есть кошелек)
                        errorMsg = data.detail.message || data.detail.error || JSON.stringify(data.detail);
                    }
                } else {
                    errorMsg = JSON.stringify(data); // Если структуры detail нет вообще
                }

                showAlert(`Ошибка: ${errorMsg}`, true);
            }
        } catch (e) {
            console.error("Сетевая ошибка:", e);
            showAlert('Ошибка сети при создании кошелька', true);
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
        try {
            // ВАЖНО: Мы отправляем только asset_id и private_key в теле JSON.
            // user_id не нужен, так как FastAPI берет его из Depends(get_current_user_id)
            const res = await fetch('/api/v1/wallets/import', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
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
        }
    });

    // Загрузка статистики профиля (Сообщения)
    async function loadStats() {
        try {
            const res = await fetch('/api/v1/profile/me/stats');
            if (res.ok) {
                const stats = await res.json();
                // Используем total_messages, так как DTO возвращает именно его
                if (stats.total_messages !== undefined) {
                    statMessages.textContent = stats.total_messages;
                } else if (stats.messages_count !== undefined) {
                    statMessages.textContent = stats.messages_count; // на случай вебсокета
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

    // Инициализация (загружаем данные при открытии страницы)
    loadAssetId().then(() => {
        loadWallets();
    });
    loadStats();

    // Получаем токен с помощью глобальной функции из main.js
    const token = getCookie('access_token');

    // Проверяем, загрузилась ли библиотека
    if (typeof io === 'undefined') {
        console.error("Ошибка: Библиотека Socket.IO не загружена! Проверьте base.html.");
    } else {
        // Инициализируем соединение с неймспейсом транзакций
        const txSocket = io("/transaction", {
            auth: { token: token },
            transports: ['websocket'] // Жестко требуем вебсокет, чтобы увидеть его в Network
        });

        // Слушаем успешное подключение
        txSocket.on("connect", () => {
            console.log("Успешно подключились к WS /transaction! ID сессии:", txSocket.id);
        });

        // Слушаем ошибки подключения (например, неверный токен)
        txSocket.on("connect_error", (err) => {
            console.error("Ошибка подключения к WS /transaction:", err.message);
        });

        // Реактивное обновление статистики
        txSocket.on("stats_updated", (data) => {
            console.log("Получены новые данные статистики по WS:", data);
            const statMessages = document.getElementById('statMessages');
            const statWallets = document.getElementById('statWallets');

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

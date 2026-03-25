document.addEventListener('DOMContentLoaded', () => {
    const btnSaveProfile = document.getElementById('btnSaveProfile');
    const inputUsername = document.getElementById('username');
    const inputEmail = document.getElementById('email');
    const inputOldPassword = document.getElementById('oldPassword');
    const inputNewPassword = document.getElementById('newPassword');
    const inputRepeatPassword = document.getElementById('repeatPassword');
    const profileAlert = document.getElementById('profileAlert');
    const profileHeaderName = document.getElementById('profileHeaderName');

    const btnRemoveAvatar = document.getElementById('btnRemoveAvatar');
    const btnUpdateAvatar = document.getElementById('btnUpdateAvatar');
    const avatarUploadInput = document.getElementById('avatarUploadInput');
    const profileAvatar = document.getElementById('profileAvatar');

    const importWalletModal = document.getElementById('importWalletModal');
    const btnOpenImportModal = document.getElementById('btnOpenImportModal');
    const btnCloseImportModal = document.getElementById('btnCloseImportModal');

    let initialUsername = '';

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

    function showAlert(message, isError = false) {
        profileAlert.style.display = 'block';
        profileAlert.style.backgroundColor = isError ? '#f8d7da' : '#d4edda';
        profileAlert.style.color = isError ? '#721c24' : '#155724';
        profileAlert.style.border = `1px solid ${isError ? '#f5c6cb' : '#c3e6cb'}`;
        profileAlert.textContent = message;

        setTimeout(() => { profileAlert.style.display = 'none'; }, 5000);
    }

    // --- Обработка кнопки SAVE ---
    btnSaveProfile.addEventListener('click', async () => {
        let hasChanges = false;

        // Вспомогательная функция для проверки на 401 ошибку
        const checkUnauthorized = (res) => {
            if (res.status === 401 || res.status === 403) {
                alert("Ваша сессия истекла. Пожалуйста, авторизуйтесь заново.");
                document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                window.location.href = "/login";
                return true;
            }
            return false;
        };

        // 1. Обновление Username
        const newUsername = inputUsername.value.trim();
        if (newUsername !== initialUsername) {
            hasChanges = true;
            try {
                const res = await fetch('/api/v1/profile/me', {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: newUsername })
                });

                if (checkUnauthorized(res)) return; // Если токен протух - прерываем

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

        // 2. Смена пароля
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

                if (checkUnauthorized(res)) return; // Если токен протух - прерываем

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

    // --- Удаление аватара ---
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

    // --- Обновление аватара ---
    btnUpdateAvatar.addEventListener('click', () => {
        avatarUploadInput.click();
    });

    avatarUploadInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        try {
            // 1. Просим у бэкенда временную ссылку для загрузки (Presigned URL)
            const extension = file.name.split('.').pop();
            const urlRes = await fetch(`/api/v1/profile/me/avatar/presigned-url?extension=${extension}&content_type=${file.type}`);

            if (urlRes.status === 401 || urlRes.status === 403) {
                alert("Сессия истекла");
                window.location.href = "/login";
                return;
            }

            if (!urlRes.ok) {
                showAlert('Ошибка при генерации ссылки для загрузки', true);
                return;
            }

            const { upload_url, public_url } = await urlRes.json();

            // 2. Браузер сам загружает файл напрямую в S3 корзину (через PUT запрос)
            const s3Res = await fetch(upload_url, {
                method: 'PUT',
                headers: {
                    'Content-Type': file.type
                },
                body: file
            });

            if (!s3Res.ok) {
                showAlert('Ошибка при загрузке картинки в облако', true);
                return;
            }

            // 3. Если загрузка успешна, говорим нашему бэкенду сохранить ссылку на аватар
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
            avatarUploadInput.value = ''; // Сбрасываем инпут
        }
    });

    // --- Модальное окно кошельков ---
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
});

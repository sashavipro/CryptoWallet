document.addEventListener('DOMContentLoaded', () => {
    // Элементы профиля
    const btnSaveProfile = document.getElementById('btnSaveProfile');
    const inputUsername = document.getElementById('username');
    const inputOldPassword = document.getElementById('oldPassword');
    const inputNewPassword = document.getElementById('newPassword');
    const inputRepeatPassword = document.getElementById('repeatPassword');
    const profileAlert = document.getElementById('profileAlert');

    // Элементы аватара
    const btnRemoveAvatar = document.getElementById('btnRemoveAvatar');
    const btnUpdateAvatar = document.getElementById('btnUpdateAvatar');
    const avatarUploadInput = document.getElementById('avatarUploadInput');
    const profileAvatar = document.getElementById('profileAvatar');

    // Модалка
    const importWalletModal = document.getElementById('importWalletModal');
    const btnOpenImportModal = document.getElementById('btnOpenImportModal');
    const btnCloseImportModal = document.getElementById('btnCloseImportModal');

    // Сохранение текущего юзернейма для проверки на изменения
    const initialUsername = inputUsername.value;

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
                if (!res.ok) {
                    const data = await res.json();
                    showAlert(`Ошибка обновления имени: ${data.detail}`, true);
                    return;
                }
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

                if (!res.ok) {
                    const data = await res.json();
                    showAlert(`Ошибка смены пароля: ${data.detail}`, true);
                    return;
                }

                // Очищаем поля после успеха
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
            // Обновляем имя в хедере
            document.querySelector('.header .username').textContent = newUsername;
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

        // TODO: В будущем здесь будет FormData и POST запрос на /api/v1/profile/me/avatar
        // Так как эндпоинта загрузки файла у нас пока нет, выведем заглушку:
        alert("Эндпоинт загрузки файла (AWS S3) находится в разработке!");

        // Сбрасываем инпут
        avatarUploadInput.value = '';
    });

    // --- Модальное окно кошельков ---
    btnOpenImportModal.addEventListener('click', () => {
        importWalletModal.style.display = 'flex';
    });

    btnCloseImportModal.addEventListener('click', () => {
        importWalletModal.style.display = 'none';
    });

    // Закрытие по клику вне модалки
    importWalletModal.addEventListener('click', (e) => {
        if (e.target === importWalletModal) {
            importWalletModal.style.display = 'none';
        }
    });
});

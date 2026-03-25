document.addEventListener('DOMContentLoaded', async () => {
    const logoutBtn = document.getElementById('logoutBtn');

    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            clearAuthAndRedirect();
        });
    }

    // Список страниц, требующих авторизации (SPA защита)
    const protectedPaths = ['/profile', '/wallets', '/ibay', '/chat'];
    const currentPath = window.location.pathname;

    if (protectedPaths.includes(currentPath)) {
        if (!getCookie('access_token')) {
            window.location.href = '/login';
            return;
        }

        try {
            // Идем на бэкенд за данными юзера
            const response = await fetch('/api/v1/profile/me', {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            });

            // Если токен истек или невалиден (устранение бесконечного цикла)
            if (response.status === 401 || response.status === 403) {
                clearAuthAndRedirect();
                return;
            }

            if (response.ok) {
                const userData = await response.json();

                // Заполняем глобальное навигационное меню
                const navUsername = document.getElementById('navUsername');
                const navAvatar = document.getElementById('navAvatar');
                if (navUsername) navUsername.textContent = userData.username;
                if (navAvatar && userData.avatar_url) navAvatar.src = userData.avatar_url;

                // Сохраняем данные глобально
                window.currentUser = userData;

                // Отправляем событие, что данные загружены (его поймает profile.js)
                document.dispatchEvent(new Event('UserDataLoaded'));
            }
        } catch (error) {
            console.error("Ошибка при получении профиля:", error);
        }
    }
});

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

function clearAuthAndRedirect() {
    document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    window.location.href = "/login";
}

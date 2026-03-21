document.addEventListener('DOMContentLoaded', () => {
    // Проверка наличия токена: если юзер уже авторизован, сразу кидаем на профиль
    if (getCookie('access_token')) {
        window.location.href = '/profile';
        return;
    }

    const loginForm = document.getElementById('loginForm');

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const rememberMe = document.getElementById('rememberMe').checked;

            try {
                // Отправляем AJAX запрос на бэкенд
                const response = await fetch('/api/v1/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ email, password })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    alert(errorData.detail || 'Ошибка авторизации. Проверьте данные.');
                    return;
                }

                const data = await response.json();

                // Формируем куку.
                // Если "Remember me" не нажато, кука удалится при закрытии браузера (сессионная).
                // Если нажато, задаем срок жизни на 30 дней.
                // Примечание: Фактическое время жизни токена контролируется бэкендом (auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES).
                let cookieString = `access_token=${data.access_token}; path=/`;

                if (rememberMe) {
                    const d = new Date();
                    d.setTime(d.getTime() + (30 * 24 * 60 * 60 * 1000));
                    cookieString += `; expires=${d.toUTCString()}`;
                }

                document.cookie = cookieString;

                // Редирект на защищенную страницу
                window.location.href = '/profile';

            } catch (error) {
                console.error('Login error:', error);
                alert('Сетевая ошибка. Попробуйте позже.');
            }
        });
    }
});

// Вспомогательная функция для чтения куки
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

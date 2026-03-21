document.addEventListener('DOMContentLoaded', () => {
    // Если токен уже есть, редирект на профиль
    if (getCookie('access_token')) {
        window.location.href = '/profile';
        return;
    }

    const registerForm = document.getElementById('registerForm');
    const errorDiv = document.getElementById('errorMessage');

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            errorDiv.style.display = 'none';

            const email = document.getElementById('email').value.trim();
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;
            const repeatPassword = document.getElementById('repeatPassword').value;

            // Фронтенд-валидация (синхронизировано с Pydantic DTO)
            if (password !== repeatPassword) {
                showError('Passwords do not match');
                return;
            }
            if (password.length < 8 || password.length > 20) {
                showError('Password must be between 8 and 20 characters');
                return;
            }
            if (username.length < 3 || username.length > 50) {
                showError('Username must be between 3 and 50 characters');
                return;
            }

            try {
                // Отправляем AJAX запрос на регистрацию
                const response = await fetch('/api/v1/auth/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ email, username, password })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    showError(errorData.detail || 'Registration failed.');
                    return;
                }

                // Получаем токен из ответа
                const data = await response.json();

                // Устанавливаем куки (делаем сессионной по умолчанию)
                document.cookie = `access_token=${data.access_token}; path=/`;

                // Автоматический редирект на профиль
                window.location.href = '/profile';

            } catch (error) {
                console.error('Registration error:', error);
                showError('Network error. Please try again later.');
            }
        });
    }

    function showError(msg) {
        errorDiv.textContent = msg;
        errorDiv.style.display = 'block';
    }
});

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

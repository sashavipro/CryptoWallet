document.addEventListener('DOMContentLoaded', () => {
    const logoutBtn = document.getElementById('logoutBtn');

    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            // Удаляем куку access_token, устанавливая дату в прошлом
            document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            // Редирект на страницу логина
            window.location.href = "/login";
        });
    }
});

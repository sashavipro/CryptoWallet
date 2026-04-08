let chatSocket = null;
let selectedImageFile = null; // Глобальная переменная для хранения выбранного файла

// Кэш для хранения Promise (защита от Race Condition)
const profileCache = {};

document.addEventListener('UserDataLoaded', initChatPage);
if (window.currentUser) { initChatPage(); }

async function initChatPage() {
    await loadChatHistory();
    initChatSocket();
    setupChatUIEvents();
}

// Умная функция получения профиля (имя + аватар) с кэшированием Promise
function fetchProfile(userId) {
    if (window.currentUser && window.currentUser.id === userId) {
        return Promise.resolve({
            username: window.currentUser.username,
            avatar: window.currentUser.avatar_url || "/static/img/default-avatar.png"
        });
    }

    if (profileCache[userId]) {
        return profileCache[userId];
    }

    profileCache[userId] = (async () => {
        try {
            const res = await fetch(`/api/v1/profile/${userId}`, {
                headers: { 'Authorization': `Bearer ${getCookie('access_token')}` }
            });
            if (res.ok) {
                const data = await res.json();
                return {
                    username: data.username,
                    avatar: data.avatar_url || "/static/img/default-avatar.png"
                };
            }
        } catch (e) {
            console.warn("Не удалось подгрузить профиль для", userId);
        }

        return {
            username: `User_${userId.substring(0,4)}`,
            avatar: "/static/img/default-avatar.png"
        };
    })();

    return profileCache[userId];
}

async function loadChatHistory() {
    try {
        const token = getCookie('access_token');
        if (!token) return;

        const response = await fetch('/api/v1/chat/messages?limit=50', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const messages = await response.json();
            document.getElementById('chatMessages').innerHTML = '';
            messages.forEach(msg => renderMessage(msg));
            setTimeout(scrollToBottom, 100);
        }
    } catch (e) {
        console.error("Ошибка загрузки истории:", e);
    }
}

function initChatSocket() {
    const token = getCookie('access_token');
    if (!token) return;

    walletSocket = io("/chat", {
        auth: { token: token },
        transports: ['websocket', 'polling']
    });

    chatSocket.on('online_users_list', (data) => {
        renderOnlineUsers(data.users);
    });

    chatSocket.on('new_message', (msg) => {
        renderMessage(msg);
        scrollToBottom();
    });
}

function renderMessage(msg) {
    const chatBox = document.getElementById('chatMessages');
    const isOwn = window.currentUser && msg.user_id === window.currentUser.id;

    let timeStr = msg.created_at
        ? new Date(msg.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
        : '---';

    const authorSpanId = `author-${crypto.randomUUID()}`;
    const avatarImgId = `avatar-${crypto.randomUUID()}`;

    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${isOwn ? 'own' : ''}`;

    const textContent = msg.text || msg.message_text || "";

    // --- ИЗМЕНЕНИЕ: ЛОГИКА ОТРИСОВКИ КАРТИНКИ ---
    let imgHtml = '';
    // Проверяем оба варианта: может прийти готовый URL из базы или просто ключ
    const imageUrl = msg.image_url || (msg.image_key ? `https://my-s3-bucket.com/${msg.image_key}` : null);

    if (imageUrl) {
        // Добавляем обработчик onload, чтобы скролл сработал ПОСЛЕ загрузки большой картинки
        imgHtml = `<img src="${imageUrl}" class="message-image" alt="Attachment" onload="scrollToBottom()">`;
    }

    // Если нет ни текста, ни картинки - не рендерим пустой пузырь
    if (!textContent && !imgHtml) return;

    msgDiv.innerHTML = `
        <div class="message-info">
            <img src="/static/img/default-avatar.png" id="${avatarImgId}" style="width: 20px; height: 20px; border-radius: 4px; object-fit: cover;">
            <span class="message-author" id="${authorSpanId}">Loading...</span>
            <span class="message-time">${timeStr}</span>
        </div>
        <div class="message-content">
            ${textContent ? escapeHtml(textContent) : ''}
            ${imgHtml}
        </div>
    `;

    chatBox.appendChild(msgDiv);

    fetchProfile(msg.user_id).then(profile => {
        const nameEl = document.getElementById(authorSpanId);
        const avatarEl = document.getElementById(avatarImgId);
        if (nameEl) nameEl.textContent = profile.username;
        if (avatarEl) avatarEl.src = profile.avatar;
    });
}

function renderOnlineUsers(users) {
    const list = document.getElementById('onlineUsersList');
    const uniqueUsers = Array.isArray(users) ? [...new Set(users)] : [];

    document.getElementById('onlineCount').textContent = uniqueUsers.length;

    let html = '';

    uniqueUsers.forEach(user => {
        let userId = typeof user === 'string' ? user : user.id;
        const nameSpanId = `online-name-${userId}`;
        const avatarImgId = `online-avatar-${userId}`;
        const defaultAvatarUrl = "/static/img/default-avatar.png";

        html += `
            <li class="online-user">
                <div class="online-avatar-wrapper">
                    <img src="${defaultAvatarUrl}" alt="Avatar" id="${avatarImgId}" class="online-avatar">
                    <div class="online-status-dot"></div>
                </div>
                <div class="online-user-info">
                    <span class="online-username" id="${nameSpanId}">Загрузка...</span>
                    <span class="online-role">В сети</span>
                </div>
            </li>
        `;
    });

    list.innerHTML = html;

    uniqueUsers.forEach(user => {
        let userId = typeof user === 'string' ? user : user.id;
        const nameSpanId = `online-name-${userId}`;
        const avatarImgId = `online-avatar-${userId}`;

        fetchProfile(userId).then(profile => {
            const el = document.getElementById(nameSpanId);
            const avatarEl = document.getElementById(avatarImgId);

            if (window.currentUser && userId === window.currentUser.id) {
                if (el) el.textContent = profile.username + " (Вы)";
            } else {
                if (el) el.textContent = profile.username;
            }
            if (avatarEl) avatarEl.src = profile.avatar;
        });
    });
}

// --- ИЗМЕНЕНИЕ: ЛОГИКА РАБОТЫ С UI КАРТИНОК ---
function setupChatUIEvents() {
    const sendBtn = document.getElementById('btnSendMsg');
    const input = document.getElementById('chatInput');
    const fileInput = document.getElementById('chatImageInput'); // Скрытый input[type=file]
    const removeImgBtn = document.getElementById('removeImageBtn');

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // Когда пользователь выбрал картинку
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                selectedImageFile = e.target.files[0];

                // Читаем файл локально для превью
                const reader = new FileReader();
                reader.onload = (event) => {
                    document.getElementById('imagePreview').src = event.target.result;
                    document.getElementById('imagePreviewContainer').style.display = 'block';
                    // Фокус обратно на инпут текста, чтобы было удобно печатать подпись
                    input.focus();
                };
                reader.readAsDataURL(selectedImageFile);
            }
        });
    }

    // Когда пользователь передумал и нажал крестик на превью
    if (removeImgBtn) {
        removeImgBtn.addEventListener('click', () => {
            clearImageSelection();
        });
    }
}

// Вспомогательная функция очистки выбранной картинки
function clearImageSelection() {
    selectedImageFile = null;
    const fileInput = document.getElementById('chatImageInput');
    if (fileInput) fileInput.value = '';
    document.getElementById('imagePreviewContainer').style.display = 'none';
    document.getElementById('imagePreview').src = '';
}

// --- ИЗМЕНЕНИЕ: ОТПРАВКА СООБЩЕНИЯ С КАРТИНКОЙ ---
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();

    // Блокируем отправку, если пусто
    if (!text && !selectedImageFile) return;

    let imageKey = null;

    // ЗАГОТОВКА ДЛЯ S3:
    if (selectedImageFile) {
        /* // 1. Получаем presigned URL от нашего бэкенда
        const presignedRes = await fetch(`/api/v1/profile/generate-upload-url?filename=${selectedImageFile.name}&file_type=chat`, {
            headers: { 'Authorization': `Bearer ${getCookie('access_token')}` }
        });
        const uploadData = await presignedRes.json();

        // 2. Отправляем сам файл напрямую в DigitalOcean Spaces (S3)
        await fetch(uploadData.upload_url, {
            method: 'PUT',
            body: selectedImageFile,
            headers: { 'Content-Type': selectedImageFile.type }
        });

        // 3. Сохраняем ключ, чтобы передать его в сокет
        imageKey = uploadData.file_key;
        */

        // ВРЕМЕННАЯ ЗАГЛУШКА ПОКА S3 НЕ РАБОТАЕТ:
        console.warn("S3 upload not yet fully integrated. Sending text only or fake key.");
        // imageKey = "fake_image_key.png"; // Можно раскомментить для теста верстки
    }

    // Отправляем всё в сокет
    if (chatSocket && chatSocket.connected) {
        // Добавляем коллбэк функцию третьим аргументом, чтобы получить ответ
        chatSocket.emit("send_message", {
            room_id: "chat_global",
            text: text,
            image_key: imageKey,
            temp_id: crypto.randomUUID()
        }, (response) => {
            // Если бэкенд отбил сообщение (например, не прошло 60 секунд)
            if (response && response.status === "error") {
                alert(response.message); // Выскочит красивое уведомление!
            } else {
                // Очищаем инпуты только если сообщение ушло успешно
                input.value = '';
                clearImageSelection();
            }
        });
    } else {
        alert("Нет подключения к чату.");
    }
}

function escapeHtml(unsafe) {
    return (unsafe || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function scrollToBottom() {
    const chatBox = document.getElementById('chatMessages');
    if (chatBox) {
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

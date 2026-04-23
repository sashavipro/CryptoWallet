let chatSocket = null;
let selectedImageFile = null;

const profileCache = {};
let currentOpenProfileId = null;

document.addEventListener('UserDataLoaded', initChatPage);
if (window.currentUser) { initChatPage(); }

async function initChatPage() {
    // 1. Проверяем доступ к чату (защита от спама 60 сек)
    if (window.currentUser && window.currentUser.has_chat_access === false) {
        const chatBox = document.getElementById('chatMessages');
        if (chatBox) {
            chatBox.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #666; text-align: center;">
                    <svg style="width: 50px; height: 50px; margin-bottom: 15px; fill: #ccc;" viewBox="0 0 24 24"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg>
                    <h3>Чат временно недоступен</h3>
                    <p>В целях защиты от спама, доступ к чату открывается через 1 минуту после регистрации.</p>
                    <p>Пожалуйста, подождите немного и обновите страницу.</p>
                </div>
            `;
        }

        // Блокируем инпуты и кнопки
        document.getElementById('chatInput').disabled = true;
        document.getElementById('btnSendMsg').disabled = true;
        document.getElementById('chatImageInput').disabled = true;
        document.getElementById('btnAttach').disabled = true;

        // Прерываем выполнение, НЕ пытаемся подключить вебсокет
        return;
    }

    // 2. Если доступ есть — штатно запускаем чат
    initChatSocket();
    await loadChatHistory();
    setupChatUIEvents();
}

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
        token = decodeURIComponent(token);
        // Мощная очистка: вырезаем слово Bearer/bearer в ЛЮБОМ регистре
        token = token.replace(/^bearer\s+/i, '').trim();
    }
    return token;
}


// ==========================================
// ЛОГИКА ПРОФИЛЕЙ И МОДАЛКИ
// ==========================================
function fetchProfile(userId, forceRefresh = false) {
    if (!forceRefresh && profileCache[userId]) {
        return profileCache[userId];
    }

    const fetchPromise = (async () => {
        try {
            const token = getToken();
            const res = await fetch(`/api/v1/profile/${userId}`, {
                headers: { 'Authorization': `Bearer ${token}` } // Теперь тут чистый токен!
            });
            if (res.ok) {
                const data = await res.json();
                return {
                    username: data.username,
                    email: data.email || "Не указана",
                    total_messages: data.total_messages || 0,
                    avatar: data.avatar_url || "/static/img/default-avatar.png"
                };
            }
        } catch (e) {
            console.warn("Не удалось подгрузить профиль", userId);
        }
        return {
            username: `User_${userId.substring(0,4)}`,
            email: "Unknown",
            total_messages: 0,
            avatar: "/static/img/default-avatar.png"
        };
    })();

    profileCache[userId] = fetchPromise;
    return fetchPromise;
}

async function updateProfileModalUI(userId) {
    try {
        const profile = await fetchProfile(userId, true);

        document.getElementById('profileModalAvatar').src = profile.avatar;
        document.getElementById('profileModalUsername').textContent = profile.username;
        document.getElementById('profileModalEmail').textContent = profile.email;
        document.getElementById('profileModalMessagesCount').textContent = profile.total_messages;

    } catch (e) {
        console.error("Ошибка обновления UI профиля", e);
    }
}

window.showUserProfile = async function(userId) {
    currentOpenProfileId = userId;
    document.getElementById('modalUserProfile').classList.remove('hidden');
    await updateProfileModalUI(userId);
};

window.closeUserProfileModal = function() {
    document.getElementById('modalUserProfile').classList.add('hidden');
    currentOpenProfileId = null;
};


// ==========================================
// ЛОГИКА WEBSOCKET СЕРВЕРА
// ==========================================

function initChatSocket() {
    const token = getToken();
    if (!token) {
        showNotification("Ошибка авторизации. Не найден токен.", true);
        return;
    }

    chatSocket = io("/chat", {
        auth: { token: token }, // Передаем ИДЕАЛЬНО ЧИСТЫЙ токен
        transports: ['websocket', 'polling']
    });

    chatSocket.on('connect', () => {
        console.log("WS подключен успешно");
        // Зеленое уведомление, что мы в сети
        showNotification("Соединение с чатом установлено!", false);
    });

    chatSocket.on('connect_error', (err) => {
        console.error("Ошибка подключения WS:", err.message);
        // Красное уведомление прямо на экран, если токен протух или сервер лежит
        showNotification("Ошибка подключения к чату: " + err.message, true);
    });

    chatSocket.on('online_users_list', (data) => {
        renderOnlineUsers(data.users);
    });

    chatSocket.on('new_message', (msg) => {
        renderMessage(msg);
        scrollToBottom();
    });

    chatSocket.on('user_profile_updated', (data) => {
        if (currentOpenProfileId === data.user_id) {
            updateProfileModalUI(data.user_id);
        }
    });
}


// ==========================================
// ИСТОРИЯ И ОТРИСОВКА СООБЩЕНИЙ
// ==========================================
async function loadChatHistory() {
    try {
        const token = getToken();
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

function renderMessage(msg) {
    const chatBox = document.getElementById('chatMessages');
    const isOwn = window.currentUser && msg.user_id === window.currentUser.id;

    let dateObj = msg.created_at ? new Date(msg.created_at) : new Date();
    const day = dateObj.getDate();
    const month = dateObj.toLocaleString('en-US', { month: 'short' });
    const hours = dateObj.getHours();
    const minutes = dateObj.getMinutes().toString().padStart(2, '0');
    let timeStr = `${day} ${month} ${hours}:${minutes}`;

    const authorSpanId = `author-${crypto.randomUUID()}`;
    const avatarImgId = `avatar-${crypto.randomUUID()}`;

    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${isOwn ? 'own' : ''}`;

    const textContent = msg.text || msg.message_text || "";

    let imgHtml = '';
    const imageUrl = msg.image_url || (msg.image_key ? `https://my-s3-bucket.com/${msg.image_key}` : null);
    if (imageUrl) {
        imgHtml = `<img src="${imageUrl}" class="message-image" alt="Attachment" onload="scrollToBottom()">`;
    }

    if (!textContent && !imgHtml) return;

    let headerHtml = `
        <span class="msg-name" id="${authorSpanId}">Loading...</span>
        <span class="msg-time">${timeStr}</span>
    `;

    let bodyHtml = `
        <img src="/static/img/default-avatar.png" id="${avatarImgId}" class="msg-avatar" onclick="showUserProfile('${msg.user_id}')" title="Профиль">
        <div class="msg-text">
            ${textContent ? escapeHtml(textContent) : ''}
            ${imgHtml}
        </div>
    `;

    msgDiv.innerHTML = `
        <div class="message-header">${headerHtml}</div>
        <div class="message-body">${bodyHtml}</div>
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
    const uniqueUsers = Array.isArray(users) ? [...new Set(users)] :[];

    let html = '';

    uniqueUsers.forEach(user => {
        let userId = typeof user === 'string' ? user : user.id;
        const nameSpanId = `online-name-${userId}`;
        const avatarImgId = `online-avatar-${userId}`;
        const defaultAvatarUrl = "/static/img/default-avatar.png";

        html += `
            <li class="online-user" onclick="showUserProfile('${userId}')">
                <img src="${defaultAvatarUrl}" alt="Avatar" id="${avatarImgId}" class="online-avatar">
                <span class="online-username" id="${nameSpanId}">Загрузка...</span>
            </li>
        `;
    });

    list.innerHTML = html;

    uniqueUsers.forEach(user => {
        let userId = typeof user === 'string' ? user : user.id;
        fetchProfile(userId).then(profile => {
            const el = document.getElementById(`online-name-${userId}`);
            const avatarEl = document.getElementById(`online-avatar-${userId}`);

            if (window.currentUser && userId === window.currentUser.id) {
                if (el) el.textContent = profile.username + " (Вы)";
            } else {
                if (el) el.textContent = profile.username;
            }
            if (avatarEl) avatarEl.src = profile.avatar;
        });
    });
}


// ==========================================
// ЛОГИКА ИНТЕРФЕЙСА (Ввод, картинки)
// ==========================================
function setupChatUIEvents() {
    const sendBtn = document.getElementById('btnSendMsg');
    const input = document.getElementById('chatInput');
    const fileInput = document.getElementById('chatImageInput');
    const attachBtn = document.getElementById('btnAttach');
    const fileNameDisplay = document.getElementById('fileNameDisplay');

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    if (attachBtn && fileInput) {
        attachBtn.addEventListener('click', () => fileInput.click());
    }

    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                selectedImageFile = e.target.files[0];
                if (!selectedImageFile.type.startsWith('image/')) {
                    alert("Пожалуйста, выберите изображение (JPG, PNG, WEBP).");
                    clearImageSelection();
                    return;
                }
                if (fileNameDisplay) {
                    fileNameDisplay.textContent = selectedImageFile.name;
                }
                input.focus();
            }
        });
    }
}

function clearImageSelection() {
    selectedImageFile = null;
    const fileInput = document.getElementById('chatImageInput');
    if (fileInput) fileInput.value = '';
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    if (fileNameDisplay) fileNameDisplay.textContent = '';
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();

    if (!text && !selectedImageFile) return;

    let imageKey = null;

    if (selectedImageFile) {
        console.warn("S3 upload is currently disabled.");
    }

    if (chatSocket) {
        if (!chatSocket.connected) {
            showNotification("Соединение с сервером устанавливается... Отправляем.", true);
        }

        chatSocket.emit("send_message", {
            room_id: "chat_global",
            text: text,
            image_key: imageKey,
            temp_id: crypto.randomUUID()
        }, (response) => {
            if (response && response.status === "error") {
                showNotification(response.message || "Ошибка при отправке сообщения", true);
            } else {
                input.value = '';
                clearImageSelection();
            }
        });
    } else {
        showNotification("Ошибка: чат не инициализирован.", true);
    }
}

function escapeHtml(unsafe) {
    return (unsafe || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function scrollToBottom() {
    const chatBox = document.getElementById('chatMessages');
    if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
}

function showNotification(message, isError = false) {
    const toast = document.createElement('div');
    toast.textContent = message;
    Object.assign(toast.style, {
        position: 'fixed', bottom: '20px', right: '20px', padding: '12px 20px',
        background: isError ? '#e74c3c' : '#2ecc71', color: 'white',
        borderRadius: '4px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        zIndex: '10000', transition: 'opacity 0.3s ease-in-out',
        fontWeight: 'bold', fontSize: '14px'
    });
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 2500);
}

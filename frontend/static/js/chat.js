let chatSocket = null;
let selectedImageFile = null;

// Кэш для хранения Promise (защита от Race Condition при запросе профилей)
const profileCache = {};

// Текущий открытый профиль в модалке
let currentOpenProfileId = null;

document.addEventListener('UserDataLoaded', initChatPage);
if (window.currentUser) { initChatPage(); }

async function initChatPage() {
    initChatSocket(); // Инициализируем сокет ПЕРЕД загрузкой истории
    await loadChatHistory();
    setupChatUIEvents();
}

// ==========================================
// ЛОГИКА ПРОФИЛЕЙ И МОДАЛКИ
// ==========================================

// Умная функция получения профиля через WEBSOCKETS с принудительным обновлением
function fetchProfile(userId, forceRefresh = false) {
    if (!forceRefresh && profileCache[userId]) {
        return profileCache[userId];
    }

    const fetchPromise = new Promise((resolve) => {
        if (!chatSocket || !chatSocket.connected) {
            resolve({
                username: `User_${userId.substring(0,4)}`,
                avatar: "/static/img/default-avatar.png",
                wallets:[],
                has_chat_access: false
            });
            return;
        }

        // Запрашиваем профиль через WebSocket
        chatSocket.emit("get_user_profile", { target_user_id: userId }, (response) => {
            if (response && response.status === "success") {
                resolve({
                    username: response.data.username,
                    avatar: response.data.avatar_url || "/static/img/default-avatar.png",
                    has_chat_access: response.data.has_chat_access,
                    wallets: response.data.wallets ||[]
                });
            } else {
                resolve({
                    username: `User_${userId.substring(0,4)}`,
                    avatar: "/static/img/default-avatar.png",
                    wallets:[],
                    has_chat_access: false
                });
            }
        });
    });

    profileCache[userId] = fetchPromise;
    return fetchPromise;
}

// Отрисовка данных внутри модалки
async function updateProfileModalUI(userId) {
    try {
        const profile = await fetchProfile(userId, true); // true = принудительно свежие данные

        document.getElementById('profileModalAvatar').src = profile.avatar;
        document.getElementById('profileModalUsername').textContent = profile.username;

        const accessEl = document.getElementById('profileModalChatAccess');
        if (accessEl) {
            if (profile.has_chat_access) {
                accessEl.textContent = "Доступ к чату: Разрешён";
                accessEl.style.color = "#28a745";
            } else {
                accessEl.textContent = "Доступ к чату: Запрещён";
                accessEl.style.color = "#e74c3c";
            }
        }

        const walletsList = document.getElementById('profileWalletsList');
        if (walletsList) {
            walletsList.innerHTML = '';

            if (profile.wallets && profile.wallets.length > 0) {
                profile.wallets.forEach(address => {
                    const li = document.createElement('li');
                    li.className = 'wallet-item';
                    li.innerHTML = `
                        <span class="wallet-address" title="${address}">${address.substring(0, 6)}...${address.slice(-4)}</span>
                        <button class="btn-copy" onclick="copyToClipboard('${address}')" title="Скопировать">
                            <svg viewBox="0 0 24 24"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>
                        </button>
                    `;
                    walletsList.appendChild(li);
                });
            } else {
                walletsList.innerHTML = '<li style="font-size: 13px; color: #888; text-align: center; padding: 10px;">У пользователя нет кошельков</li>';
            }
        }
    } catch (e) {
        console.error("Ошибка обновления UI профиля", e);
    }
}

// Открытие модалки профиля по клику на пользователя
window.showUserProfile = async function(userId) {
    currentOpenProfileId = userId;
    document.getElementById('modalUserProfile').classList.remove('hidden');
    await updateProfileModalUI(userId);
};

// Закрытие модалки
window.closeUserProfileModal = function() {
    document.getElementById('modalUserProfile').classList.add('hidden');
    currentOpenProfileId = null;
};


// ==========================================
// ЛОГИКА WEBSOCKET СЕРВЕРА
// ==========================================

function initChatSocket() {
    const token = getCookie('access_token');
    if (!token) return;

    chatSocket = io("/chat", {
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

    // РЕАКТИВНОЕ ОБНОВЛЕНИЕ МОДАЛКИ (Event-Driven)
    chatSocket.on('user_profile_updated', (data) => {
        // Если пришло событие, что профиль обновился, и мы прямо сейчас на него смотрим — обновляем модалку
        if (currentOpenProfileId === data.user_id) {
            console.log("Получено WS событие: обновление профиля для", data.user_id);
            updateProfileModalUI(data.user_id);
        }
    });
}

// ==========================================
// ИСТОРИЯ И ОТРИСОВКА СООБЩЕНИЙ
// ==========================================

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

    let headerHtml = isOwn
        ? `<span class="msg-time">${timeStr}</span><span class="msg-name" id="${authorSpanId}">Loading...</span>`
        : `<span class="msg-name" id="${authorSpanId}">Loading...</span><span class="msg-time">${timeStr}</span>`;

    let bodyHtml = `
        ${!isOwn ? `<img src="/static/img/default-avatar.png" id="${avatarImgId}" class="msg-avatar" onclick="showUserProfile('${msg.user_id}')" title="Профиль">` : ''}
        <div class="msg-text">
            ${textContent ? escapeHtml(textContent) : ''}
            ${imgHtml}
        </div>
        ${isOwn ? `<img src="/static/img/default-avatar.png" id="${avatarImgId}" class="msg-avatar" onclick="showUserProfile('${msg.user_id}')" title="Профиль">` : ''}
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
        console.warn("S3 upload is currently disabled. Sending fake image key.");
        // imageKey = "fake_chat_image.png";
    }

    if (chatSocket && chatSocket.connected) {
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
        showNotification("Нет подключения к чату.", true);
    }
}


// ==========================================
// УТИЛИТЫ
// ==========================================

window.copyToClipboard = function(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification("Адрес скопирован!", false);
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
};

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

function escapeHtml(unsafe) {
    return (unsafe || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function scrollToBottom() {
    const chatBox = document.getElementById('chatMessages');
    if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

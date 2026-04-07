let chatSocket = null;
let selectedImageFile = null;

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

    // Если Promise уже есть в кэше, возвращаем его
    if (profileCache[userId]) {
        return profileCache[userId];
    }

    // Создаем новый Promise и сразу кладем его в кэш
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

        // Fallback в случае ошибки
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

    chatSocket = io("http://localhost:8004/chat", {
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
    let imgHtml = '';
    if (msg.image_url) {
        imgHtml = `<img src="${msg.image_url}" class="message-image" alt="Attachment">`;
    }

    msgDiv.innerHTML = `
        <div class="message-info">
            <img src="/static/img/default-avatar.png" id="${avatarImgId}" style="width: 20px; height: 20px; border-radius: 4px; object-fit: cover;">
            <span class="message-author" id="${authorSpanId}">Loading...</span>
            <span class="message-time">${timeStr}</span>
        </div>
        <div class="message-content">
            ${escapeHtml(textContent)}
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

function setupChatUIEvents() {
    const sendBtn = document.getElementById('btnSendMsg');
    const input = document.getElementById('chatInput');
    const fileInput = document.getElementById('chatImageInput');
    const removeImgBtn = document.getElementById('removeImageBtn');

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                selectedImageFile = e.target.files[0];
                const reader = new FileReader();
                reader.onload = (e) => {
                    document.getElementById('imagePreview').src = e.target.result;
                    document.getElementById('imagePreviewContainer').style.display = 'block';
                };
                reader.readAsDataURL(selectedImageFile);
            }
        });
    }

    if (removeImgBtn) {
        removeImgBtn.addEventListener('click', () => {
            selectedImageFile = null;
            if (fileInput) fileInput.value = '';
            document.getElementById('imagePreviewContainer').style.display = 'none';
        });
    }
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (!text && !selectedImageFile) return;

    let imageKey = null;

    if (chatSocket && chatSocket.connected) {
        chatSocket.emit("send_message", {
            room_id: "chat_global",
            text: text,
            image_key: imageKey,
            temp_id: crypto.randomUUID()
        });
        input.value = '';
        if (document.getElementById('removeImageBtn')) {
            document.getElementById('removeImageBtn').click();
        }
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

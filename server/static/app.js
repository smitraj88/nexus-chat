const socket = io();
let currentUser = "";
let currentFriend = "";
let unreadCounts = {};

// Screens
const loginScreen = document.getElementById('login-screen');
const appScreen = document.getElementById('app-screen');
const chatView = document.getElementById('chat-view');

let isSignUpMode = false;

function toggleAuthMode() {
    isSignUpMode = !isSignUpMode;
    const title = document.getElementById('auth-title');
    const btn = document.getElementById('auth-btn');
    const emailInput = document.getElementById('email');
    const toggleText = document.querySelector('#login-form-container p');
    
    if (isSignUpMode) {
        title.textContent = "Sign Up";
        btn.textContent = "Sign Up";
        emailInput.style.display = 'block';
        toggleText.innerHTML = `Already have an account? <span style="color: #9b5de5; font-weight: bold;">Log in</span>`;
    } else {
        title.textContent = "Log In";
        btn.textContent = "Log In";
        emailInput.style.display = 'none';
        toggleText.innerHTML = `Don't have an account? <span style="color: #9b5de5; font-weight: bold;">Sign up</span>`;
    }
}

async function submitAuth() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const email = document.getElementById('email').value.trim();
    
    if (!username || !password) return alert('Username and Password required');
    if (isSignUpMode && !email) return alert('Email required for sign up');
    
    const url = isSignUpMode ? '/signup' : '/login';
    const payload = { username, password };
    if (isSignUpMode) payload.email = email;
    
    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        if (res.ok) {
            if (isSignUpMode) {
                alert("Account created! Please log in.");
                toggleAuthMode(); // switch back to login
            } else {
                currentUser = username;
                socket.emit('user_connected', { username: currentUser });
                loginScreen.classList.remove('active');
                appScreen.classList.add('active');
                loadContacts();
            }
        } else {
            alert(data.message || "Authentication failed");
        }
    } catch (e) {
        alert("Server error: " + e.message);
    }
}

async function loadContacts() {
    try {
        const res = await fetch(`/contacts/${currentUser}`);
        const data = await res.json();
        const contacts = data.contacts || [];
        
        const chatList = document.getElementById('chat-list');
        chatList.innerHTML = '';
        
        for (const contact of contacts) {
            renderContactItem(contact);
        }
    } catch (e) {
        console.error(e);
    }
}

async function renderContactItem(contact) {
    const chatList = document.getElementById('chat-list');
    
    // Remove if exists to move to top
    const existing = document.getElementById(`contact-${contact}`);
    if (existing) existing.remove();
    
    const div = document.createElement('div');
    div.className = 'chat-item';
    div.id = `contact-${contact}`;
    div.onclick = () => openChat(contact);
    
    const unread = unreadCounts[contact] || 0;
    const avatarUrl = await getAvatarUrl(contact);
    
    div.innerHTML = `
        <img src="${avatarUrl}" class="avatar" style="object-fit: cover;">
        <div class="chat-item-info">
            <div class="chat-item-header">
                <span class="chat-name">${contact}</span>
            </div>
            <div class="chat-message-preview">Tap to view chat...</div>
        </div>
        ${unread > 0 ? `<div class="unread-badge">${unread}</div>` : ''}
        <button class="icon-btn" style="color: #94a3b8; font-size: 20px; padding: 0 10px;" onclick="event.stopPropagation(); openContactMenu('${contact}')">⋮</button>
    `;
    
    // Insert at top
    chatList.prepend(div);
}

async function getAvatarUrl(username) {
    try {
        const res = await fetch(`/avatar/${username}`);
        const data = await res.json();
        return data.avatar;
    } catch {
        return `https://api.dicebear.com/7.x/adventurer/svg?seed=${username}`;
    }
}

async function openChat(contact) {
    currentFriend = contact;
    unreadCounts[contact] = 0;
    renderContactItem(contact); // update badge
    
    document.getElementById('chat-name').textContent = contact;
    
    const avatarUrl = await getAvatarUrl(contact);
    document.getElementById('chat-avatar').src = avatarUrl;
    
    appScreen.classList.remove('active');
    chatView.classList.add('active');
    chatView.classList.remove('slide-right');
    
    socket.emit('join_room', { username: currentUser, friend: contact });
    
    // Fetch last seen
    const res = await fetch(`/last_seen/${contact}`);
    const statusData = await res.json();
    document.getElementById('chat-status').textContent = statusData.status || "Offline";
    
    loadMessages();
}

function closeChat() {
    chatView.classList.add('slide-right');
    setTimeout(() => {
        chatView.classList.remove('active');
        appScreen.classList.add('active');
        currentFriend = "";
    }, 300);
}

async function loadMessages() {
    const res = await fetch(`/private_messages?user1=${currentUser}&user2=${currentFriend}`);
    const data = await res.json();
    
    window.currentMessageCount = data.messages.length;
    const chatBox = document.getElementById('chat-messages');
    chatBox.innerHTML = '';
    data.messages.forEach(msg => appendMessage(msg.user, msg.message, msg.timestamp));
    
    fetch('/mark_read', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({user: currentUser, friend: currentFriend})
    });
}

function appendMessage(sender, text, timestamp) {
    const chatBox = document.getElementById('chat-messages');
    
    if (!timestamp) {
        const d = new Date();
        timestamp = d.getHours().toString().padStart(2, '0') + ':' + d.getMinutes().toString().padStart(2, '0');
    }
    
    const div = document.createElement('div');
    div.className = `msg ${sender === currentUser ? 'msg-out' : 'msg-in'}`;
    
    // Check if message has an image URL
    if (text.includes("🖼")) {
        div.innerHTML = `<img src="${text.split(' ')[text.split(' ').length-1]}" style="max-width: 100%; border-radius: 10px; margin-bottom: 5px;"><br><span class="msg-time">${timestamp}</span>`;
    } else if (text.includes("🎤")) {
        div.innerHTML = `<audio controls src="${text.split(' ')[text.split(' ').length-1]}" style="max-width: 100%; margin-bottom: 5px; height: 40px;"></audio><br><span class="msg-time">${timestamp}</span>`;
    } else if (text.includes("📄")) {
        const parts = text.split('|');
        const urlPart = parts[0].trim();
        const url = urlPart.split(' ').pop();
        const filename = parts.length > 1 ? parts[1].trim() : "Document";
        
        div.innerHTML = `
            <a href="${url}" target="_blank" style="text-decoration: none; color: inherit;">
                <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 10px; display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 24px;">📄</span>
                    <div style="word-break: break-all; font-weight: bold; text-decoration: underline;">${filename}</div>
                </div>
            </a>
            <br><span class="msg-time">${timestamp}</span>
        `;
    } else {
        div.innerHTML = `${text} <span class="msg-time">${timestamp}</span>`;
    }
    
    // Add onclick to show message actions
    div.onclick = () => openMsgAction(sender, text, timestamp, div);
    
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// === PROFILE VIEW ===
async function viewProfile(name) {
    if (!name) return;
    document.getElementById('profile-view-name').textContent = name;
    
    const avatarUrl = await getAvatarUrl(name);
    document.getElementById('profile-view-img').src = avatarUrl;
    
    document.getElementById('profile-modal').classList.add('active');
    document.getElementById('profile-modal').classList.remove('slide-right');
}

function closeProfile() {
    document.getElementById('profile-modal').classList.add('slide-right');
    setTimeout(() => {
        document.getElementById('profile-modal').classList.remove('active');
    }, 300);
}

// === MESSAGE ACTIONS (Edit/Delete) ===
let selectedMsg = null;
let selectedMsgDiv = null;

function openMsgAction(sender, text, timestamp, div) {
    selectedMsg = { sender, text, timestamp };
    selectedMsgDiv = div;
    
    // Only allow editing/deleting own messages
    if (sender === currentUser) {
        document.getElementById('msg-edit-btn').style.display = 'block';
    } else {
        document.getElementById('msg-edit-btn').style.display = 'none';
    }
    
    document.getElementById('msg-action-modal').classList.add('active');
    document.getElementById('msg-action-modal').classList.remove('slide-right');
}

function closeMsgAction() {
    document.getElementById('msg-action-modal').classList.add('slide-right');
    setTimeout(() => {
        document.getElementById('msg-action-modal').classList.remove('active');
    }, 300);
}

async function editMessage() {
    if (selectedMsg.sender !== currentUser) return;
    const newText = prompt("Edit your message:", selectedMsg.text);
    if (newText && newText !== selectedMsg.text) {
        socket.emit('edit_message', {
            user: currentUser,
            friend: currentFriend,
            old_message: selectedMsg.text,
            new_message: newText
        });
        closeMsgAction();
        loadMessages(); // Refresh chat immediately
    }
}

async function deleteMessage(forEveryone) {
    if (forEveryone && selectedMsg.sender !== currentUser) {
        alert("You can only delete your own messages for everyone.");
        return;
    }
    
    if (forEveryone) {
        socket.emit('delete_message', {
            user: selectedMsg.sender,
            friend: currentFriend,
            message: selectedMsg.text,
            timestamp: selectedMsg.timestamp,
            for_everyone: true
        });
    } else {
        // Delete for me
        selectedMsgDiv.remove();
    }
    closeMsgAction();
}

socket.on('message_deleted', () => loadMessages());
socket.on('message_edited', () => loadMessages());

// === MEDIA PREVIEW (Photo/Audio) ===
let pendingMediaText = "";

function showPreview(htmlContent, messageText) {
    document.getElementById('preview-content').innerHTML = htmlContent;
    pendingMediaText = messageText;
    document.getElementById('preview-modal').classList.add('active');
    document.getElementById('preview-modal').classList.remove('slide-right');
}

function cancelPreview() {
    pendingMediaText = "";
    document.getElementById('preview-modal').classList.add('slide-right');
    setTimeout(() => {
        document.getElementById('preview-modal').classList.remove('active');
    }, 300);
}

function sendPreview() {
    if (pendingMediaText) {
        socket.emit('private_message', { user: currentUser, friend: currentFriend, message: pendingMediaText });
    }
    cancelPreview();
}

// === NEW FEATURES ===
async function openSettings() {
    document.getElementById('my-name').textContent = currentUser;
    const avatarUrl = await getAvatarUrl(currentUser);
    document.getElementById('my-avatar').src = avatarUrl;
    
    document.getElementById('settings-modal').classList.add('active');
    document.getElementById('settings-modal').classList.remove('slide-right');
}

function closeSettings() {
    document.getElementById('settings-modal').classList.add('slide-right');
    setTimeout(() => {
        document.getElementById('settings-modal').classList.remove('active');
    }, 300);
}

function logout() {
    closeSettings();
    socket.emit('disconnect_request'); // Optional custom event
    location.reload(); // Refresh the page to return to login
}

// === LIVE CAMERA ===
let videoStream = null;

async function openLiveCamera() {
    document.getElementById('camera-modal').classList.add('active');
    document.getElementById('camera-modal').classList.remove('slide-right');
    const video = document.getElementById('live-video');
    try {
        videoStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
        video.srcObject = videoStream;
    } catch (e) {
        alert("Camera access denied or unavailable: " + e.message);
        closeLiveCamera();
    }
}

function closeLiveCamera() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
    document.getElementById('camera-modal').classList.add('slide-right');
    setTimeout(() => {
        document.getElementById('camera-modal').classList.remove('active');
    }, 300);
}

function captureLivePhoto() {
    const video = document.getElementById('live-video');
    const canvas = document.getElementById('camera-canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    
    // Convert to blob and upload
    canvas.toBlob(async (blob) => {
        closeLiveCamera(); // stop camera
        
        const formData = new FormData();
        const uniqueFilename = `live_photo_${Date.now()}.jpg`;
        formData.append('file', blob, uniqueFilename);
        
        try {
            const res = await fetch('/upload', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.filename) {
                const url = `/uploads/${data.filename}`;
                const html = `<img src="${url}" style="max-width: 100%; border-radius: 10px;">`;
                showPreview(html, `🖼 Sent an image: ${url}`);
            }
        } catch (e) {
            alert("Upload failed: " + e.message);
        }
    }, 'image/jpeg', 0.8);
}

// === RAW WAV AUDIO RECORDING (FOOLPROOF) ===
let audioContext;
let audioInput;
let processor;
let recordingData = [];
let isRecording = false;

function encodeWav(samples, sampleRate) {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);
    const writeString = (view, offset, string) => {
        for (let i = 0; i < string.length; i++) view.setUint8(offset + i, string.charCodeAt(i));
    };
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(view, 8, 'WAVE');
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true); // 1 channel
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(view, 36, 'data');
    view.setUint32(40, samples.length * 2, true);
    let offset = 44;
    for (let i = 0; i < samples.length; i++, offset += 2) {
        let s = Math.max(-1, Math.min(1, samples[i]));
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    return new Blob([view], { type: 'audio/wav' });
}

async function startWavRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        audioInput = audioContext.createMediaStreamSource(stream);
        processor = audioContext.createScriptProcessor(4096, 1, 1);
        
        recordingData = [];
        processor.onaudioprocess = function(e) {
            if (!isRecording) return;
            recordingData.push(new Float32Array(e.inputBuffer.getChannelData(0)));
        };
        
        audioInput.connect(processor);
        processor.connect(audioContext.destination);
        
        isRecording = true;
        document.getElementById('voice-btn').style.color = '#ef4444';
        document.getElementById('voice-btn').textContent = '⏹';
    } catch (err) {
        alert("Microphone access denied: " + err.message);
    }
}

// === DOCUMENT UPLOAD ===
async function uploadDocument(input) {
    if (!input.files || !input.files[0]) return;
    const file = input.files[0];
    const formData = new FormData();
    const safeName = file.name.replace(/[^a-zA-Z0-9.\-_]/g, '_');
    const uniqueFilename = `doc_${Date.now()}_${safeName}`;
    formData.append('file', file, uniqueFilename);
    
    try {
        const res = await fetch('/upload', { method: 'POST', body: formData });
        const data = await res.json();
        if (data.filename) {
            const url = `/uploads/${data.filename}`;
            const html = `
                <div style="background: #1e293b; padding: 15px; border-radius: 10px; display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 30px;">📄</span>
                    <div style="color: white; word-break: break-all;">${file.name}</div>
                </div>
            `;
            showPreview(html, `📄 Sent a document: ${url} | ${file.name}`);
        }
    } catch (e) {
        alert("Document upload failed: " + e.message);
    }
    input.value = ''; // Reset input so user can upload same file again if needed
}

async function stopWavRecording() {
    isRecording = false;
    document.getElementById('voice-btn').style.color = '#9b5de5';
    document.getElementById('voice-btn').textContent = '🎤';
    
    processor.disconnect();
    audioInput.disconnect();
    
    // Stop mic
    audioInput.mediaStream.getTracks().forEach(track => track.stop());
    
    if (audioContext && audioContext.state !== 'closed') {
        audioContext.close();
    }
    
    // Flatten array
    let totalLength = 0;
    for (const buf of recordingData) totalLength += buf.length;
    
    if (totalLength === 0) {
        alert("Audio recording failed (0 bytes).");
        return;
    }
    
    const samples = new Float32Array(totalLength);
    let offset = 0;
    for (const buf of recordingData) {
        samples.set(buf, offset);
        offset += buf.length;
    }
    
    const wavBlob = encodeWav(samples, audioContext.sampleRate);
    recordingData = [];
    
    const formData = new FormData();
    formData.append('file', wavBlob, `voice_${Date.now()}.wav`);
    
    try {
        const res = await fetch('/upload', { method: 'POST', body: formData });
        const data = await res.json();
        if (data.filename) {
            const url = `/uploads/${data.filename}`;
            const html = `<audio controls src="${url}" preload="auto"></audio>`;
            showPreview(html, `🎤 Voice Message: ${url}`);
        }
    } catch(e) {
        alert("Upload failed: " + e.message);
    }
}

async function toggleRecording() {
    if (isRecording) {
        stopWavRecording();
    } else {
        startWavRecording();
    }
}

// === CONTACT ACTIONS ===
async function addNewContact() {
    const contactName = prompt("Enter the username of the person you want to add:");
    if (!contactName || contactName.trim() === "") return;
    
    try {
        const res = await fetch('/contacts', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: currentUser, contact: contactName.trim()})
        });
        
        if (res.ok) {
            loadContacts();
            alert(contactName + " has been added to your contacts!");
        } else {
            const data = await res.json();
            alert("Failed to add contact: " + (data.message || "Unknown error"));
        }
    } catch (e) {
        alert("Error adding contact: " + e.message);
    }
}

let menuContact = "";

function openContactMenu(contact) {
    menuContact = contact;
    document.getElementById('contact-menu-name').textContent = contact;
    document.getElementById('contact-menu-modal').classList.add('active');
    document.getElementById('contact-menu-modal').classList.remove('slide-right');
}

function closeContactMenu() {
    document.getElementById('contact-menu-modal').classList.add('slide-right');
    setTimeout(() => {
        document.getElementById('contact-menu-modal').classList.remove('active');
    }, 300);
}

async function editContact() {
    const newName = prompt(`Enter new name for ${menuContact}:`, menuContact);
    if (newName && newName !== menuContact) {
        await fetch('/contacts', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: currentUser, old_contact: menuContact, new_contact: newName})
        });
        closeContactMenu();
        loadContacts();
    }
}

async function blockContact() {
    if (confirm(`Are you sure you want to block ${menuContact}?`)) {
        await fetch('/block', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: currentUser, contact: menuContact})
        });
        alert(`${menuContact} blocked.`);
        closeContactMenu();
    }
}

async function deleteContact() {
    if (confirm(`Are you sure you want to delete ${menuContact}?`)) {
        await fetch('/contacts', {
            method: 'DELETE',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: currentUser, contact: menuContact})
        });
        closeContactMenu();
        loadContacts();
    }
}

async function viewBlocked() {
    const res = await fetch(`/blocked/${currentUser}`);
    const data = await res.json();
    if (data.blocked && data.blocked.length > 0) {
        const contact = prompt(`Blocked Contacts:\n${data.blocked.join(', ')}\n\nType a name to unblock:`);
        if (contact) {
            await fetch('/unblock', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username: currentUser, contact: contact})
            });
            alert(`${contact} unblocked.`);
        }
    } else {
        alert("You have no blocked contacts.");
    }
}

async function sendMessage() {
    const input = document.getElementById('msg-input');
    const text = input.value.trim();
    if (!text) return;
    
    // Optimistic UI update
    const d = new Date();
    let hours = d.getHours();
    let ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12;
    let mins = d.getMinutes().toString().padStart(2, '0');
    appendMessage(currentUser, text, `${hours}:${mins} ${ampm}`);
    
    try {
        await fetch('/send_message', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                user: currentUser,
                friend: currentFriend,
                message: text
            })
        });
    } catch(e) {
        console.error("Failed to send:", e);
    }
    
    input.value = '';
}

socket.on('private_message', (data) => {
    const sender = data.user;
    
    // If it's a message for the current open chat
    if (sender === currentFriend || (sender === currentUser && data.friend === currentFriend)) {
        appendMessage(sender, data.message, data.timestamp);
    } 
    
    // Determine the "other" person to bump to top / add unread
    let otherPerson = sender === currentUser ? data.friend : sender;
    
    if (otherPerson && otherPerson !== currentFriend && sender !== currentUser) {
        unreadCounts[otherPerson] = (unreadCounts[otherPerson] || 0) + 1;
    }
    
    if (otherPerson) {
        renderContactItem(otherPerson);
    }
});

// === SERVERLESS POLLER ===
setInterval(async () => {
    if (!currentUser) return;

    if (currentFriend && chatView.classList.contains('active')) {
        const res = await fetch(`/private_messages?user1=${currentUser}&user2=${currentFriend}`);
        const data = await res.json();
        if (window.currentMessageCount !== data.messages.length) {
            window.currentMessageCount = data.messages.length;
            const chatBox = document.getElementById('chat-messages');
            chatBox.innerHTML = '';
            data.messages.forEach(msg => appendMessage(msg.user, msg.message, msg.timestamp));
            
            fetch('/mark_read', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({user: currentUser, friend: currentFriend})
            });
        }
    }

    if (appScreen.classList.contains('active')) {
        const res2 = await fetch(`/unread_counts/${currentUser}`);
        const data2 = await res2.json();
        let changed = false;
        for (let contact in data2.unread) {
            if (unreadCounts[contact] !== data2.unread[contact]) {
                unreadCounts[contact] = data2.unread[contact];
                changed = true;
            }
        }
        if (changed) loadContacts();
    }
}, 3000);

// === AVATAR OPTIONS ===
async function openAvatarOptions() {
    document.getElementById('avatar-options-modal').classList.add('active');
    document.getElementById('avatar-options-modal').classList.remove('slide-right');
}

function closeAvatarOptions() {
    document.getElementById('avatar-options-modal').classList.add('slide-right');
    setTimeout(() => { document.getElementById('avatar-options-modal').classList.remove('active'); }, 300);
}

function openAvatarSelector() {
    closeAvatarOptions();
    const grid = document.getElementById('cartoon-avatar-grid');
    grid.innerHTML = '';
    const styles = ['adventurer', 'bottts', 'fun-emoji', 'pixel-art', 'lorelei'];
    for(let i=0; i<15; i++) {
        const seed = Math.random().toString(36).substring(7);
        const style = styles[Math.floor(Math.random() * styles.length)];
        const url = `https://api.dicebear.com/7.x/${style}/svg?seed=${seed}`;
        const img = document.createElement('img');
        img.src = url;
        img.style.width = '100%';
        img.style.borderRadius = '50%';
        img.style.backgroundColor = '#1e293b';
        img.style.cursor = 'pointer';
        img.onclick = () => saveAvatar(url);
        grid.appendChild(img);
    }
    document.getElementById('avatar-selector-modal').classList.add('active');
    document.getElementById('avatar-selector-modal').classList.remove('slide-right');
}

function closeAvatarSelector() {
    document.getElementById('avatar-selector-modal').classList.add('slide-right');
    setTimeout(() => { document.getElementById('avatar-selector-modal').classList.remove('active'); }, 300);
}

async function uploadCustomAvatar(input) {
    if (!input.files || !input.files[0]) return;
    const file = input.files[0];
    const formData = new FormData();
    const uniqueFilename = `avatar_${Date.now()}_${file.name.replace(/[^a-zA-Z0-9.\-_]/g, '_')}`;
    formData.append('file', file, uniqueFilename);
    
    try {
        const res = await fetch('/upload', { method: 'POST', body: formData });
        const data = await res.json();
        if (data.filename) {
            const url = `/uploads/${data.filename}`;
            saveAvatar(url);
        }
    } catch (e) {
        alert("Upload failed: " + e.message);
    }
    input.value = '';
    closeAvatarOptions();
}

async function deleteAvatar() {
    const url = `https://api.dicebear.com/7.x/adventurer/svg?seed=${currentUser}`;
    saveAvatar(url);
    closeAvatarOptions();
}

async function saveAvatar(url) {
    await fetch('/avatar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: currentUser, avatar: url })
    });
    
    document.getElementById('my-avatar').src = url;
    
    if (document.getElementById('avatar-selector-modal').classList.contains('active')) {
        closeAvatarSelector();
    }
    
    // Refresh UI to show new avatar everywhere locally
    loadContacts(); 
}

let isSetupMode = false;
let autoLockTimer;

// --- Auto-Lock (5 Mins Inactivity) ---
function resetAutoLock() {
    clearTimeout(autoLockTimer);
    autoLockTimer = setTimeout(() => {
        if (document.getElementById('dashboard-view').style.display === "flex") lockSession();
    }, 300000);
}
window.onload = resetAutoLock;
document.onmousemove = resetAutoLock;
document.onkeypress = resetAutoLock;

async function initApp() {
    let setupComplete = await eel.is_setup()();
    if (!setupComplete) {
        isSetupMode = true;
        document.getElementById('auth-subtitle').innerText = "Create a master password";
        document.getElementById('auth-btn').innerText = "Create Vault";
        document.getElementById('setup-fields').style.display = "block";
        setupPasswordStrength();
    } else {
        document.getElementById('forgot-btn').style.display = "block";
        checkLockoutStatus();
    }

    document.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') handleAuth();
    });
}
initApp();

// --- NEW FEATURE LOGIC ---
async function openActivityLog() {
    let logs = await eel.get_activity_log()();
    let container = document.getElementById('log-list');
    container.innerHTML = "";

    if (logs.length === 0) {
        container.innerHTML = "<p style='color: gray; text-align: center;'>No activity recorded yet.</p>";
    } else {
        logs.forEach(log => {
            let [action, time] = log;
            // Determine icon based on action
            let icon = "⚪";
            if (action.includes("Locked")) icon = "🔒";
            else if (action.includes("Unlocked")) icon = "🔓";
            else if (action.includes("Failed")) icon = "❌";
            else if (action.includes("Success")) icon = "✅";

            container.innerHTML += `
                <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px; margin-bottom: 8px; display: flex; align-items: center; border-left: 3px solid rgba(255,255,255,0.1);">
                    <div style="margin-right: 15px; font-size: 18px;">${icon}</div>
                    <div>
                        <div style="font-size: 14px; font-weight: 600;">${action}</div>
                        <div style="font-size: 11px; color: #7f8c8d;">${time}</div>
                    </div>
                </div>`;
        });
    }
    document.getElementById('log-modal').style.display = "flex";
}

function closeActivityLog() {
    document.getElementById('log-modal').style.display = "none";
}

async function triggerBackup() {
    showToast("Select a destination folder (like Google Drive)...", "success");
    let result = await eel.create_backup()();
    if (result.success) {
        showToast("Database safely backed up!", "success");
    } else if (result.error !== "Cancelled") {
        showToast("Backup failed: " + result.error, "error");
    }
}

// --- Beautiful Custom Confirm Dialog ---
function customConfirm(title, message, okText = "Confirm", isDanger = true) {
    return new Promise((resolve) => {
        const modal = document.getElementById('confirm-modal');
        const titleEl = document.getElementById('confirm-title');
        const msgEl = document.getElementById('confirm-message');
        const okBtn = document.getElementById('confirm-ok-btn');
        const cancelBtn = document.getElementById('confirm-cancel-btn');

        titleEl.innerText = title;
        titleEl.style.color = isDanger ? "#e74c3c" : "#3498db";
        msgEl.innerText = message;
        okBtn.innerText = okText;
        okBtn.className = isDanger ? "action-btn btn-lock" : "action-btn btn-unlock";
        modal.style.display = "flex";

        const handleOk = () => { cleanup(); resolve(true); };
        const handleCancel = () => { cleanup(); resolve(false); };
        const cleanup = () => {
            modal.style.display = "none";
            okBtn.removeEventListener('click', handleOk);
            cancelBtn.removeEventListener('click', handleCancel);
        };

        okBtn.addEventListener('click', handleOk);
        cancelBtn.addEventListener('click', handleCancel);
    });
}

async function checkLockoutStatus() {
    let response = await eel.do_login("")();
    if (response.locked) triggerLockout(response.time_left);
}

function togglePwd(inputId, iconElement) {
    let input = document.getElementById(inputId);
    if (input.type === "password") {
        input.type = "text";
        iconElement.innerText = "🙈";
    } else {
        input.type = "password";
        iconElement.innerText = "👁️";
    }
}

function setupPasswordStrength() {
    document.getElementById('password').addEventListener('input', function(e) {
        let val = e.target.value;
        let bar = document.getElementById('strength-bar');
        let text = document.getElementById('strength-text');

        let strength = 0;
        if (val.length >= 8) strength += 25;
        if (val.match(/[A-Z]/)) strength += 25;
        if (val.match(/[0-9]/)) strength += 25;
        if (val.match(/[^A-Za-z0-9]/)) strength += 25;

        bar.style.width = strength + '%';
        if (strength <= 25) { bar.style.backgroundColor = '#e74c3c'; text.innerText = 'Weak'; text.style.color = '#e74c3c'; }
        else if (strength <= 50) { bar.style.backgroundColor = '#f39c12'; text.innerText = 'Moderate'; text.style.color = '#f39c12'; }
        else if (strength <= 75) { bar.style.backgroundColor = '#3498db'; text.innerText = 'Good'; text.style.color = '#3498db'; }
        else { bar.style.backgroundColor = '#2ecc71'; text.innerText = 'Strong'; text.style.color = '#2ecc71'; }
    });
}

function showToast(message, type="success") {
    let container = document.getElementById('toast-container');
    let toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerText = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 500);
    }, 3500);
}

function triggerLockout(seconds) {
    let btn = document.getElementById('auth-btn');
    let input = document.getElementById('password');
    btn.disabled = true;
    input.disabled = true;

    let timer = setInterval(() => {
        if (seconds <= 0) {
            clearInterval(timer);
            btn.disabled = false;
            input.disabled = false;
            btn.innerText = "Unlock Vault";
            showToast("You can try again.", "success");
        } else {
            btn.innerText = `Locked... wait ${seconds}s`;
            seconds--;
        }
    }, 1000);
}

async function handleAuth() {
    let pwd = document.getElementById('password').value;
    let btn = document.getElementById('auth-btn');

    if (btn.disabled) return;

    if (pwd.length < 8) {
        showToast("Password must be at least 8 characters.", "error");
        return;
    }
    btn.innerText = "Processing...";

    if (isSetupMode) {
        let conf = document.getElementById('confirm-password').value;
        let hint = document.getElementById('password-hint').value;
        if (pwd !== conf) {
            showToast("Passwords do not match.", "error");
            btn.innerText = "Create Vault";
            return;
        }
        await eel.do_setup(pwd, hint)();
        showToast("Vault initialized! Logging you in...", "success");
        setTimeout(() => window.location.reload(), 1500);
    } else {
        let response = await eel.do_login(pwd)();

        if (response.success) {
            document.getElementById('auth-view').style.display = "none";
            document.getElementById('dashboard-view').style.display = "flex";
            showToast("Access Granted.", "success");
            document.getElementById('password').value = "";
            loadVaults();
        } else if (response.locked) {
            showToast("Too many failed attempts.", "error");
            triggerLockout(response.time_left);
        } else {
            showToast(`Invalid Password. Attempts left: ${response.attempts_left}`, "error");
            btn.innerText = "Unlock Vault";
            document.getElementById('password').value = "";
        }
    }
}

async function handleForgotPwd() {
    let hint = await eel.get_hint()();
    let msg = hint ? `Your password hint is: "${hint}"\n\n` : "You did not set a password hint.\n\n";
    msg += "Because VaultX uses military-grade encryption, your password cannot be recovered.\n\nWould you like to FACTORY RESET the app? (Warning: You will lose access to all currently locked folders forever).";

    let reset = await customConfirm("Factory Reset?", msg, "RESET APP", true);
    if (reset) {
        await eel.factory_reset()();
        showToast("VaultX has been factory reset. Restarting...", "success");
        setTimeout(() => window.location.reload(), 2000);
    }
}

let currentVaults = [];
async function loadVaults() {
    currentVaults = await eel.get_vaults()();
    renderVaults(currentVaults);
}

function renderVaults(vaultsToRender) {
    let container = document.getElementById('vault-list');

    document.getElementById('stat-total-vaults').innerText = vaultsToRender.length;
    let totalFiles = vaultsToRender.reduce((sum, v) => sum + v[4], 0);
    document.getElementById('stat-total-files').innerText = totalFiles.toLocaleString();

    if (vaultsToRender.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📭</div>
                <div class="empty-text">No vaults secured yet.</div>
                <div style="font-size: 14px; color: #7f8c8d; margin-top: 10px;">
                    Click the <strong>'+ Add Folder'</strong> button in the sidebar to secure your first folder.
                </div>
            </div>`;
        return;
    }

    container.innerHTML = "";
    vaultsToRender.forEach(v => {
        let [id, name, path, is_locked, files] = v;
        let actionsHtml = is_locked ?
            `<div class="status-locked">🔒 Locked</div>
             <button class="action-btn btn-unlock" onclick="processVault(${id}, '${path.replace(/\\/g, '\\\\')}', 'unlock')">Unlock</button>` :
            `<div class="status-unlocked">🔓 Unlocked</div>
             <div>
                <button class="action-btn btn-remove" onclick="removeVault(${id})">Remove</button>
                <button class="action-btn btn-lock" onclick="processVault(${id}, '${path.replace(/\\/g, '\\\\')}', 'lock')">Lock</button>
             </div>`;

        container.innerHTML += `
            <div class="vault-card">
                <div class="vault-name">${name} <span style="font-size:12px; color:gray; font-weight: normal;">(${files.toLocaleString()} files)</span></div>
                <div class="vault-path">${path}</div>
                <div class="card-actions">${actionsHtml}</div>
            </div>`;
    });
}

function filterVaults() {
    let query = document.getElementById('vault-search').value.toLowerCase();
    let filtered = currentVaults.filter(v => v[1].toLowerCase().includes(query) || v[2].toLowerCase().includes(query));
    renderVaults(filtered);
}

async function addFolder() {
    let path = await eel.browse_folder()();
    if (path) processVault(null, path, 'lock', true);
}

async function removeVault(id) {
    let confirmRemove = await customConfirm(
        "Remove Vault?",
        "Remove this folder from VaultX? Your files will remain unlocked on your PC.",
        "Remove Vault",
        false
    );

    if(confirmRemove) {
        await eel.remove_vault(id)();
        showToast("Vault removed.", "success");
        loadVaults();
    }
}

async function processVault(id, path, action, isNew=false) {
    document.getElementById('loading-modal').style.display = "flex";
    document.getElementById('modal-title').innerText = action === 'lock' ? "Encrypting Vault..." : "Decrypting Vault...";
    await eel.process_vault(id, path, action, isNew)();
    document.getElementById('loading-modal').style.display = "none";
    showToast(`Folder successfully ${action}ed!`, "success");
    loadVaults();
}

function lockSession() { window.location.reload(); }

eel.expose(updateProgressUI);
function updateProgressUI(percent, text) {
    document.getElementById('progress-fill').style.width = `${percent * 100}%`;
    document.getElementById('modal-percent').innerText = `${Math.floor(percent * 100)}%`;
    document.getElementById('modal-file').innerText = text;
}
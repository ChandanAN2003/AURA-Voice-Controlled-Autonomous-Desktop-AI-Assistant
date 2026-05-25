const DEFAULT_API = "https://handball-gown-bobtail.ngrok-free.dev/api";
let API_BASE = localStorage.getItem("aura_api_base") || DEFAULT_API;

const chatContainer = document.getElementById("chat-container");
const cmdInput = document.getElementById("cmd-input");
const btnSend = document.getElementById("btn-send");

const btnListen = document.getElementById("btn-listen");
const btnWakeToggle = document.getElementById("btn-wake-toggle");
const btnRefresh = document.getElementById("btn-refresh");

const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");

const cpuFill = document.getElementById("cpu-fill");
const cpuText = document.getElementById("cpu-text");
const ramFill = document.getElementById("ram-fill");
const ramText = document.getElementById("ram-text");

const historyList = document.getElementById("history-list");
const logsContainer = document.getElementById("logs-container");

const voiceConfirm = document.getElementById("voice-confirm-banner");
const voiceText = document.getElementById("voice-confirm-text");
const btnVcYes = document.getElementById("btn-voice-confirm");
const btnVcNo = document.getElementById("btn-voice-reject");

// Settings Modal DOM Elements
const btnSettings = document.getElementById("btn-settings");
const settingsModal = document.getElementById("settings-modal");
const btnCloseSettings = document.getElementById("btn-close-settings");
const settingsApiUrl = document.getElementById("settings-api-url");
const btnResetSettings = document.getElementById("btn-reset-settings");
const btnSaveSettings = document.getElementById("btn-save-settings");

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const hasSpeechAPI = !!SpeechRecognition;
const WAKE_WORDS = ["hey aura", "hi aura", "aura", "wake up aura"];

let isListening = false;
let wakeEnabled = false;
let wakeRecognition = null;
let cmdRecognition = null;

let isDemoMode = false;
let simulatedHistory = [
    { command: "open brave", timestamp: Date.now() - 1800000, status: "SUCCESS" },
    { command: "open paint and write hi", timestamp: Date.now() - 3600000, status: "SUCCESS" },
    { command: "screenshot", timestamp: Date.now() - 7200000, status: "SUCCESS" }
];

function init() {
    updateLog("System initializing...", "system");
    updateStatus("thinking", "Connecting...");
    
    // Test backend connection
    fetch(`${API_BASE}/history`, {
        headers: { "ngrok-skip-browser-warning": "69420" }
    })
    .then(r => r.json())
    .then(data => {
        updateLog("Local PC connected successfully.", "success");
        updateStatus("idle", "Ready");
        renderHistory(data.history || []);
        startMetricPolling();
    })
    .catch(() => {
        // Backend offline -> Switch to interactive Demo Mode!
        isDemoMode = true;
        updateLog("Local PC offline. Booting interactive Demo Mode...", "system");
        updateStatus("idle", "Demo Active");
        renderHistory(simulatedHistory);
        startMetricPolling();
    });
}

function startMetricPolling() {
    setInterval(() => {
        if (isDemoMode) {
            // Randomize telemetry to make the dashboard look alive and fully functional
            const cpu = Math.floor(Math.random() * (35 - 12 + 1)) + 12;
            const ram = Math.floor(Math.random() * (56 - 48 + 1)) + 48;
            if(cpuText) cpuText.innerText = `${cpu}%`;
            if(cpuFill) cpuFill.style.width = `${cpu}%`;
            if(ramText) ramText.innerText = `${ram}%`;
            if(ramFill) ramFill.style.width = `${ram}%`;
            return;
        }

        fetch(`${API_BASE}/system_stats`, {
            headers: { "ngrok-skip-browser-warning": "69420" }
        }).then(r=>r.json()).then(d=>{
            if(cpuText) cpuText.innerText = `${d.cpu_percent}%`;
            if(cpuFill) cpuFill.style.width = `${d.cpu_percent}%`;
            if(ramText) ramText.innerText = `${d.ram_percent}%`;
            if(ramFill) ramFill.style.width = `${d.ram_percent}%`;
        }).catch(()=>{});
    }, 2000);
}

function updateStatus(state, msg) {
    statusDot.className = `dot ${state}`;
    if (state === "idle" && isDemoMode) {
        statusDot.style.background = "var(--accent)";
        statusText.innerHTML = "Demo Active <span style='font-size:10px; opacity:0.6;'>(Offline)</span>";
    } else {
        statusDot.style.background = ""; // Clear fallback
        statusText.innerText = msg;
    }
}

function updateLog(msg, type="action") {
    const div = document.createElement("div");
    div.className = `log-line ${type}`;
    div.innerHTML = `<i class="fas fa-terminal"></i> <span>${msg}</span>`;
    logsContainer.prepend(div);
}

function appendChatBubble(role, htmlMsg) {
    const emptyState = document.querySelector('.empty-state');
    if(emptyState) emptyState.style.display = 'none';

    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-msg ${role}`;
    
    msgDiv.innerHTML = `
        <div class="avatar ${role}">${role==='ai'?'<i class="fas fa-microchip"></i>':'<i class="fas fa-user"></i>'}</div>
        <div class="msg-bubble">${htmlMsg}</div>
    `;

    chatContainer.insertBefore(msgDiv, chatContainer.lastElementChild);
    chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: 'smooth'
    });

    return msgDiv.querySelector('.msg-bubble');
}

function executeCommand(cmd) {
    if(!cmd.trim()) return;
    cmdInput.value = "";
    voiceConfirm.classList.add("hidden");
    clearTimeout(voiceConfirm._timer);

    appendChatBubble("user", cmd);
    
    if (isDemoMode) {
        runSimulatedExecution(cmd);
        return;
    }
    
    const aiBubble = appendChatBubble("ai", '<i class="fas fa-circle-notch fa-spin"></i> Analyzing intent...');
    updateStatus("thinking", "Analyzing...");
    updateLog(`Executing: ${cmd}`, "action");

    fetch(`${API_BASE}/execute`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "ngrok-skip-browser-warning": "69420"
        },
        body: JSON.stringify({ command: cmd })
    })
    .then(r => r.json())
    .then(data => {
        if(data.status === "SUCCESS") {
            updateStatus("executing", "Success");
            aiBubble.innerHTML = data.message;
            updateLog("Execution SUCCESS.", "success");
        } else {
            updateStatus("error", "Failed");
            aiBubble.innerHTML = `<span style="color:var(--error);"><i class="fas fa-exclamation-triangle"></i> ${data.message}</span>`;
            updateLog(`Error: ${data.message}`, "error");
        }
        setTimeout(()=>updateStatus("idle", "Ready"), 3000);
        fetchHistory();
    })
    .catch(e => {
        updateStatus("error", "API Error");
        aiBubble.innerHTML = `<span style="color:var(--error);">Network connection failed.</span>`;
        updateLog(e.message, "error");
        setTimeout(()=>updateStatus("idle", "Ready"), 3000);
    });
}

function runSimulatedExecution(cmd) {
    const aiBubble = appendChatBubble("ai", '<i class="fas fa-circle-notch fa-spin"></i> Parsing instruction...');
    updateStatus("thinking", "Demo Planning");
    updateLog(`[DemoPlanner] Analyzing: "${cmd}"`, "action");

    // Phase 1: Planning (800ms)
    setTimeout(() => {
        updateLog(`[DemoPlanner] Dynamic sequence created: [DesktopActionSequence]`, "action");
        updateLog(`[DemoPlanner] Schema matches: Rule-based planning`, "success");
    }, 800);

    // Phase 2: Execution (1800ms)
    setTimeout(() => {
        updateStatus("executing", "Demo Execution");
        const lowerCmd = cmd.toLowerCase();
        
        if (lowerCmd.includes("brave") || lowerCmd.includes("chrome") || lowerCmd.includes("browser")) {
            updateLog("[DesktopExecutor] Step 1: Searching for local browser shortcut...", "action");
            updateLog("[DesktopExecutor] Step 2: Executing pyautogui double-click event", "action");
        } else if (lowerCmd.includes("notepad")) {
            updateLog("[DesktopExecutor] Step 1: Initializing 'notepad.exe'", "action");
            updateLog("[DesktopExecutor] Step 2: Typing local character buffer sequence", "action");
        } else if (lowerCmd.includes("screenshot")) {
            updateLog("[DesktopExecutor] Step 1: Capturing screen coordinates", "action");
            updateLog("[DesktopExecutor] Step 2: Writing frame buffer to screenshot.png", "action");
        } else {
            updateLog("[DesktopExecutor] Step 1: Navigating Windows shell parameters", "action");
            updateLog("[DesktopExecutor] Step 2: Sending hotkey inputs...", "action");
        }
    }, 1800);

    // Phase 3: Reflection & Success (2800ms)
    setTimeout(() => {
        updateLog("[SelfReflection] Capturing screen and invoking OCR verify...", "action");
        updateLog("[SelfReflection] Success criteria verified (Score: 100%)", "success");
    }, 2800);

    // Phase 4: Output Rendering (3800ms)
    setTimeout(() => {
        updateStatus("executing", "Success");
        updateLog(`[Demo] Execution SUCCESS.`, "success");
        
        const lowerCmd = cmd.toLowerCase();
        if (lowerCmd.includes("brave") || lowerCmd.includes("chrome") || lowerCmd.includes("browser")) {
            aiBubble.innerHTML = "I have successfully launched your web browser on your Windows host desktop!";
        } else if (lowerCmd.includes("notepad")) {
            aiBubble.innerHTML = "I have opened Notepad and successfully typed your requested text sequence!";
        } else if (lowerCmd.includes("screenshot")) {
            aiBubble.innerHTML = "Captured screenshot successfully! Screen perceptual context has been saved to FAISS vector memory.";
        } else {
            aiBubble.innerHTML = `I have successfully completed your desktop automation sequence for: "${cmd}"!`;
        }

        // Add to simulated history
        simulatedHistory.unshift({
            command: cmd,
            timestamp: Date.now(),
            status: "SUCCESS"
        });
        
        renderHistory(simulatedHistory);
        setTimeout(() => updateStatus("idle", "Demo Active"), 3000);
    }, 3800);
}

function fetchHistory() {
    if (isDemoMode) {
        renderHistory(simulatedHistory);
        return;
    }
    
    fetch(`${API_BASE}/history`, {
        headers: { "ngrok-skip-browser-warning": "69420" }
    })
    .then(r => r.json())
    .then(data => {
        renderHistory(data.history || []);
    })
    .catch(() => {
        if (!isDemoMode) {
            isDemoMode = true;
            renderHistory(simulatedHistory);
        }
    });
}

function renderHistory(history) {
    historyList.innerHTML = "";
    (history || []).forEach(item => {
        const div = document.createElement("div");
        div.className = "history-item";
        div.innerHTML = `
            <span class="h-cmd">${item.command}</span>
            <div class="h-meta">
                <span class="h-time">${new Date(item.timestamp).toLocaleTimeString()}</span>
                <span class="h-badge ${item.status}">${item.status}</span>
            </div>
        `;
        historyList.appendChild(div);
    });
}

// ---------------- VOICE LOGIC ----------------

function buildWake() {
    if(!hasSpeechAPI) return null;
    const r = new SpeechRecognition();
    r.continuous = true;
    r.onresult = (e) => {
        for(let i=e.resultIndex; i<e.results.length; i++) {
            if(e.results[i].isFinal && WAKE_WORDS.some(w => e.results[i][0].transcript.toLowerCase().includes(w))) {
                handleWake();
            }
        }
    };
    r.onerror = () => { if(wakeEnabled) setTimeout(restartWake, 1000); };
    r.onend = () => { if(wakeEnabled && !isListening) restartWake(); };
    return r;
}

function buildCmd() {
    if(!hasSpeechAPI) return null;
    const r = new SpeechRecognition();
    r.interimResults = true;
    r.onresult = (e) => {
        let i_str='', f_str='';
        for(let i=e.resultIndex; i<e.results.length; i++) {
            if(e.results[i].isFinal) f_str += e.results[i][0].transcript;
            else i_str += e.results[i][0].transcript;
        }
        if(i_str) cmdInput.value = i_str;
        if(f_str.trim()) {
            cmdInput.value = f_str.trim();
            showVC(f_str.trim());
        }
    };
    r.onerror = () => stopListen();
    r.onend = () => stopListen();
    r.onstart = () => {
        isListening = true;
        btnListen.classList.add("listening-active");
        btnListen.innerHTML = `<i class="fas fa-stop-circle"></i> Listening...`;
        updateStatus("listening", "Listening...");
    };
    return r;
}

function handleWake() {
    if(isListening) return;
    try {
        const cx = new (window.AudioContext || window.webkitAudioContext)();
        const o = cx.createOscillator(); o.connect(cx.destination);
        o.frequency.value = 800; o.start(); o.stop(cx.currentTime + 0.1);
    } catch(e){}
    updateLog("Wake word detected", "system");
    if(wakeRecognition) { try{wakeRecognition.stop();}catch(e){} }
    setTimeout(startListen, 200);
}

function startListen() {
    if(isListening) {
        if(cmdRecognition) cmdRecognition.stop();
        stopListen();
        return;
    }
    cmdRecognition = buildCmd();
    if(cmdRecognition) {
        try{ cmdRecognition.start(); }catch(e){}
    } else {
        if (isDemoMode) {
            updateLog("Simulating voice capture fallback...", "system");
            setTimeout(() => { showVC("open brave"); }, 1500);
            return;
        }
        updateLog("Using fallback audio API", "system");
        fetch(`${API_BASE}/listen`, {
            headers: { "ngrok-skip-browser-warning": "69420" }
        }).then(r=>r.json()).then(d=>{ if(d.heard) showVC(d.heard); });
    }
}

function stopListen() {
    isListening = false;
    btnListen.classList.remove("listening-active");
    btnListen.innerHTML = `<i class="fas fa-play"></i> Tap to Speak`;
    if(statusDot.className.includes("listening")) updateStatus("idle", "Ready");
    if(wakeEnabled) restartWake();
}

function showVC(text) {
    stopListen();
    voiceText.innerText = `"${text}"`;
    voiceConfirm.classList.remove("hidden");
    voiceConfirm._timer = setTimeout(() => { executeCommand(text); }, 4000);
}

function toggleWake() {
    wakeEnabled = !wakeEnabled;
    if(wakeEnabled) {
        if(!hasSpeechAPI) return;
        btnWakeToggle.classList.add("wake-active");
        btnWakeToggle.querySelector("span").innerText = "ON";
        wakeRecognition = buildWake();
        try{wakeRecognition.start();}catch(e){}
    } else {
        btnWakeToggle.classList.remove("wake-active");
        btnWakeToggle.querySelector("span").innerText = "OFF";
        if(wakeRecognition){try{wakeRecognition.stop();}catch(e){}}
    }
}

function restartWake() { setTimeout(()=>{ if(wakeEnabled && !isListening && wakeRecognition){ try{wakeRecognition.start();}catch(e){} } }, 300); }

// Settings Event Listeners
btnSettings.addEventListener("click", () => {
    settingsApiUrl.value = localStorage.getItem("aura_api_base") || "";
    settingsModal.classList.remove("hidden");
});

btnCloseSettings.addEventListener("click", () => {
    settingsModal.classList.add("hidden");
});

settingsModal.addEventListener("click", (e) => {
    if (e.target === settingsModal) settingsModal.classList.add("hidden");
});

btnResetSettings.addEventListener("click", () => {
    localStorage.removeItem("aura_api_base");
    API_BASE = DEFAULT_API;
    settingsApiUrl.value = "";
    settingsModal.classList.add("hidden");
    updateLog("Connection reset to default cloud endpoint.", "system");
    
    // Attempt to recheck and re-initialize connection
    isDemoMode = false;
    init();
});

btnSaveSettings.addEventListener("click", () => {
    const customUrl = settingsApiUrl.value.trim();
    if (customUrl === "" || customUrl.toLowerCase() === "demo") {
        localStorage.removeItem("aura_api_base");
        API_BASE = DEFAULT_API;
    } else {
        localStorage.setItem("aura_api_base", customUrl);
        API_BASE = customUrl;
    }
    settingsModal.classList.add("hidden");
    updateLog(`Target endpoint updated to: ${API_BASE}`, "system");
    
    // Attempt to recheck and re-initialize connection
    isDemoMode = false;
    init();
});

// Listeners
btnSend.addEventListener("click", () => executeCommand(cmdInput.value));
cmdInput.addEventListener("keydown", (e) => { if(e.key==="Enter") executeCommand(cmdInput.value); });
btnListen.addEventListener("click", startListen);
btnWakeToggle.addEventListener("click", toggleWake);
btnRefresh.addEventListener("click", fetchHistory);

btnVcYes.addEventListener("click", () => executeCommand(voiceText.innerText.replace(/"/g, '')));
btnVcNo.addEventListener("click", () => {
    voiceConfirm.classList.add("hidden");
    clearTimeout(voiceConfirm._timer);
    cmdInput.value = "";
    updateLog("Voice aborted", "system");
});

init();


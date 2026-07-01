# app.py
from flask import Flask, render_template_string, Response, jsonify, request
from engine import STATE, SYSTEM_LOGS, PROFILES, AVAILABLE_COMMAND_HOOKS, FINGER_LABELS, generate_frames, \
    execute_command, save_profiles
import cv2

app = Flask(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nova Assistant</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        let currentEditingKey = "Profile 1";
        let activeHooksList = [];

        function updateDashboardState() {
            fetch('/api/state')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('status-badge').innerText = data.assistant_status;
                    document.getElementById('hover-badge').innerText = data.hover_state || "None";
                    document.getElementById('profile-badge').innerText = data.current_user;

                    const engineText = data.face_recognition_enabled ? "Tracking Active" : "Tracking Terminated";
                    document.getElementById('engine-badge').innerText = engineText;

                    const btn = document.getElementById('toggle-face-btn');
                    if(data.face_recognition_enabled) {
                        btn.innerText = "Disable Face Detection";
                        btn.className = "w-full py-2.5 px-4 bg-rose-950/40 hover:bg-rose-900/40 text-rose-300 font-medium rounded-xl border border-rose-800/40 transition-all text-xs cursor-pointer";
                    } else {
                        btn.innerText = "Enable Face Detection";
                        btn.className = "w-full py-2.5 px-4 bg-emerald-950/40 hover:bg-emerald-900/40 text-emerald-300 font-medium rounded-xl border border-emerald-800/40 transition-all text-xs cursor-pointer";
                    }

                    const camBtn = document.getElementById('toggle-camera-btn');
                    if(data.camera_enabled !== false) {
                        camBtn.innerText = "Disable Camera";
                        camBtn.className = "w-full py-2.5 px-4 bg-rose-950/40 hover:bg-rose-900/40 text-rose-300 font-medium rounded-xl border border-rose-800/40 transition-all text-xs cursor-pointer";
                    } else {
                        camBtn.innerText = "Enable Camera";
                        camBtn.className = "w-full py-2.5 px-4 bg-emerald-950/40 hover:bg-emerald-900/40 text-emerald-300 font-medium rounded-xl border border-emerald-800/40 transition-all text-xs cursor-pointer";
                    }
                });
        }

        function fetchLogs() {
            fetch('/api/logs')
                .then(res => res.json())
                .then(logs => {
                    const consoleEl = document.getElementById('web-console');
                    if (consoleEl.innerText !== logs.join('\\n')) {
                        consoleEl.innerText = logs.join('\\n') || "Initializing runtime connection stream...";
                        consoleEl.scrollTop = consoleEl.scrollHeight;
                    }
                });
        }

        function toggleFaceEngine() {
            fetch('/api/toggle_face', { method: 'POST' }).then(() => updateDashboardState());
        }

        function toggleCameraEngine() {
            fetch('/api/toggle_camera', { method: 'POST' }).then(() => updateDashboardState());
        }

        function refreshDropdowns(profileObj) {
            const dynamicHooks = [...activeHooksList, ...Object.keys(profileObj.custom_commands || {})];

            const dropdownContainers = document.querySelectorAll('.gesture-select-menu');
            dropdownContainers.forEach(selectEl => {
                const currentVal = selectEl.getAttribute('data-pending-val') || "unassigned";
                selectEl.innerHTML = '<option value="">(Unassigned)</option>';

                dynamicHooks.forEach(hook => {
                    const opt = document.createElement('option');
                    opt.value = hook;
                    opt.innerText = hook;
                    if(hook === currentVal) opt.selected = true;
                    selectEl.appendChild(opt);
                });
            });
        }

        function selectEditorProfile(profileKey) {
            currentEditingKey = profileKey;

            ['Profile 1', 'Profile 2', 'Profile 3'].forEach(k => {
                const btn = document.getElementById(`tab-${k}`);
                if (k === profileKey) {
                    btn.className = "px-4 py-2 text-xs font-bold rounded-xl bg-orange-500/20 border border-orange-500/40 text-orange-300 shadow-inner";
                } else {
                    btn.className = "px-4 py-2 text-xs font-medium rounded-xl bg-[#161413] border border-[#322d2a] text-stone-400 hover:text-stone-200 transition-all";
                }
            });

            fetch('/api/profiles')
                .then(res => res.json())
                .then(profiles => {
                    const p = profiles[profileKey];
                    document.getElementById('profile-name-input').value = p.name;

                    const patterns = ["01000", "01100", "01110", "01111", "11111", "10001", "01001", "10000", "00000"];
                    patterns.forEach(pat => {
                        const el = document.getElementById(`select-pattern-${pat}`);
                        if(el) {
                            el.setAttribute('data-pending-val', p.gestures[pat] || "");
                        }
                    });

                    refreshDropdowns(p);
                    renderCustomCommandsList(p.custom_commands || {});
                });
        }

        function renderCustomCommandsList(customCmds) {
            const listEl = document.getElementById('custom-commands-registry');
            listEl.innerHTML = "";

            const keys = Object.keys(customCmds);
            if(keys.length === 0) {
                listEl.innerHTML = `<div class="text-[11px] text-stone-500 italic font-mono p-3 bg-[#161413]/50 border border-[#322d2a]/60 rounded-xl">No custom app bindings created inside this slot profile.</div>`;
                return;
            }

            keys.forEach(k => {
                const item = customCmds[k];
                const div = document.createElement('div');
                div.className = "flex justify-between items-center bg-[#161413] p-2.5 rounded-xl border border-[#322d2a] text-xs font-mono shadow-sm";
                div.innerHTML = `
                    <div class="truncate max-w-[180px]">
                        <span class="text-orange-400 font-bold">${k}</span> 
                        <span class="text-stone-500 text-[10px] ml-1">(${item.type})</span>
                    </div>
                    <button onclick="deleteCustomCommand('${k}')" class="text-rose-400 hover:text-rose-300 px-2 cursor-pointer font-sans text-[11px] font-medium transition-colors">✕ Remove</button>
                `;
                listEl.appendChild(div);
            });
        }

        function createCustomCommand() {
            const label = document.getElementById('cmd-label-input').value.trim().toLowerCase().replace(/[^a-z0-9_]/g, "");
            const type = document.getElementById('cmd-type-select').value;
            const target = document.getElementById('cmd-target-input').value.trim();

            if(!label || !target) {
                alert("Please fill out both the macro nickname identifier and target pathway line.");
                return;
            }

            fetch('/api/create_custom_command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: currentEditingKey, label: label, type: type, target: target })
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    document.getElementById('cmd-label-input').value = "";
                    document.getElementById('cmd-target-input').value = "";
                    selectEditorProfile(currentEditingKey);
                }
            });
        }

        function deleteCustomCommand(cmdLabel) {
            fetch('/api/delete_custom_command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: currentEditingKey, label: cmdLabel })
            }).then(() => selectEditorProfile(currentEditingKey));
        }

        function saveProfileModifications() {
            const currentName = document.getElementById('profile-name-input').value;
            const targetGestures = {};

            const patterns = ["01000", "01100", "01110", "01111", "11111", "10001", "01001", "10000", "00000"];
            patterns.forEach(pat => {
                const el = document.getElementById(`select-pattern-${pat}`);
                if(el) targetGestures[pat] = el.value;
            });

            fetch('/api/update_profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    key: currentEditingKey,
                    name: currentName,
                    gestures: targetGestures
                })
            }).then(() => {
                updateDashboardState();
                selectEditorProfile(currentEditingKey);
                alert("Configuration matrices saved persistently to server cache store!");
            });
        }

        function activateProfile() {
            fetch('/api/activate_profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: currentEditingKey })
            }).then(() => updateDashboardState());
        }

        window.onload = () => {
            fetch('/api/hooks').then(res => res.json()).then(hooks => {
                activeHooksList = hooks;
                selectEditorProfile("Profile 1");
            });
            setInterval(updateDashboardState, 1000);
            setInterval(fetchLogs, 500);
        };
    </script>
</head>
<body class="bg-[#181615] text-[#e5e0db] min-h-screen flex flex-col font-sans selection:bg-orange-500/20">

    <header class="border-b border-[#2c2724] bg-[#221f1e]/80 backdrop-blur-md sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="h-2.5 w-2.5 bg-orange-400 rounded-full shadow-[0_0_8px_rgba(251,146,60,0.5)]"></div>
                <span class="font-bold tracking-wide text-lg text-stone-200">Nova Assistant</span>
            </div>
            <div class="text-xs text-stone-400 font-mono bg-[#161413] border border-[#322d2a] px-3 py-1 rounded-full">
                Workspace: <span class="text-orange-400/90 font-medium">Dynamic Customizer v3</span>
            </div>
        </div>
    </header>

    <main class="flex-1 max-w-7xl w-full mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">

        <div class="lg:col-span-7 flex flex-col space-y-6">
            <div class="bg-[#221f1e] border border-[#2c2724] rounded-[2rem] overflow-hidden shadow-xl shrink-0">
                <div class="px-5 py-4 border-b border-[#161413] bg-[#221f1e]/40">
                    <h2 class="font-semibold text-xs tracking-wider uppercase text-stone-400 flex items-center gap-2">📷 Core Camera Processing Stream</h2>
                </div>
                <div class="bg-[#161413] flex items-center justify-center p-3">
                    <img src="/video_feed" class="w-full h-auto rounded-xl max-h-[440px] object-contain bg-black shadow-inner border border-[#2c2724]" alt="Camera Layer"/>
                </div>
            </div>

            <div class="bg-[#221f1e] border border-[#2c2724] rounded-[2rem] p-5 shadow-xl flex flex-col flex-1 min-h-[12rem]">
                <div class="flex justify-between items-center border-b border-[#161413] pb-3 mb-3 shrink-0">
                    <h3 class="text-xs font-bold tracking-wider uppercase text-stone-400 flex items-center gap-2">
                        <span class="inline-block w-1.5 h-1.5 rounded-full bg-orange-400"></span> Live Core Console Logs
                    </h3>
                    <span class="text-[10px] font-mono text-stone-500 bg-[#161413] px-2 py-0.5 rounded border border-[#2c2724]">stdout active</span>
                </div>
                <pre id="web-console" class="bg-[#161413] text-orange-200/80 font-mono text-xs p-4 rounded-xl border border-[#2c2724] flex-1 overflow-y-auto scroll-smooth whitespace-pre-wrap leading-relaxed shadow-inner custom-scrollbar">Connecting to logging core...</pre>
            </div>
        </div>

        <div class="lg:col-span-5 flex flex-col space-y-6">
            <div class="bg-[#221f1e] border border-[#2c2724] rounded-[2rem] p-5 shadow-xl shrink-0">
                <div class="grid grid-cols-2 gap-3">
                    <div class="bg-[#161413] p-3.5 rounded-xl border border-[#2c2724]">
                        <div class="text-[10px] text-stone-500 uppercase font-bold tracking-wider mb-0.5">System State</div>
                        <div id="status-badge" class="text-xs font-bold text-orange-400">Loading...</div>
                    </div>
                    <div class="bg-[#161413] p-3.5 rounded-xl border border-[#2c2724]">
                        <div class="text-[10px] text-stone-500 uppercase font-bold tracking-wider mb-0.5">Active User</div>
                        <div id="profile-badge" class="text-xs font-bold text-emerald-400">Loading...</div>
                    </div>
                    <div class="bg-[#161413] p-3.5 rounded-xl border border-[#2c2724]">
                        <div class="text-[10px] text-stone-500 uppercase font-bold tracking-wider mb-0.5">Last Action</div>
                        <div id="hover-badge" class="text-[11px] font-mono text-rose-400 truncate">Loading...</div>
                    </div>
                    <div class="bg-[#161413] p-3.5 rounded-xl border border-[#2c2724]">
                        <div class="text-[10px] text-stone-500 uppercase font-bold tracking-wider mb-0.5">Face Engine</div>
                        <div id="engine-badge" class="text-xs font-bold text-amber-300">Loading...</div>
                    </div>
                </div>
            </div>

            <div class="bg-[#221f1e] border border-[#2c2724] rounded-[2rem] p-5 space-y-4 shadow-xl shrink-0">
                <h3 class="text-xs font-bold uppercase tracking-wider text-stone-400 border-b border-[#161413] pb-2">🛠️ Custom Automation Action Creator</h3>

                <div class="grid grid-cols-3 gap-2">
                    <input id="cmd-label-input" type="text" placeholder="e.g. open_spotify" class="col-span-2 bg-[#161413] border border-[#322d2a] rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:border-orange-500/50 text-stone-100 font-mono"/>
                    <select id="cmd-type-select" class="bg-[#161413] border border-[#322d2a] text-xs text-stone-300 rounded-lg px-1.5 py-1.5 cursor-pointer">
                        <option value="url">Web URL</option>
                        <option value="terminal">Shell/App</option>
                    </select>
                </div>
                <div class="flex gap-2">
                    <input id="cmd-target-input" type="text" placeholder="https://open.spotify.com  OR  open -a Spotify" class="flex-1 bg-[#161413] border border-[#322d2a] rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:border-orange-500/50 font-mono text-stone-300"/>
                    <button onclick="createCustomCommand()" class="bg-emerald-900/40 hover:bg-emerald-900/60 text-emerald-300 border border-emerald-800/40 font-bold text-xs px-4 rounded-lg transition-colors cursor-pointer">Add</button>
                </div>

                <div id="custom-commands-registry" class="space-y-1.5 max-h-24 overflow-y-auto pr-1 custom-scrollbar">
                </div>
            </div>

            <div class="bg-[#221f1e] border border-[#2c2724] rounded-[2rem] p-5 space-y-4 shadow-xl flex-1 flex flex-col">
                <div class="grid grid-cols-3 gap-1.5 p-1 bg-[#161413] rounded-xl border border-[#2c2724] shrink-0">
                    <button id="tab-Profile 1" onclick="selectEditorProfile('Profile 1')" class="px-2 py-1 text-xs font-medium rounded-lg transition-all cursor-pointer">Slot 1</button>
                    <button id="tab-Profile 2" onclick="selectEditorProfile('Profile 2')" class="px-2 py-1 text-xs font-medium rounded-lg transition-all cursor-pointer">Slot 2</button>
                    <button id="tab-Profile 3" onclick="selectEditorProfile('Profile 3')" class="px-2 py-1 text-xs font-medium rounded-lg transition-all cursor-pointer">Slot 3</button>
                </div>

                <div class="flex flex-col gap-1.5 shrink-0">
                    <label class="text-[10px] font-bold uppercase tracking-wider text-stone-500">Slot Custom Name Label</label>
                    <input id="profile-name-input" type="text" class="w-full bg-[#161413] border border-[#322d2a] rounded-lg px-3 py-1.5 text-xs text-stone-100 font-medium focus:outline-none focus:border-orange-500/50"/>
                </div>

                <div class="space-y-2 flex-1 overflow-y-auto pr-1 border-t border-[#161413] pt-3 custom-scrollbar min-h-[12rem]">
                    <label class="text-[10px] font-bold uppercase tracking-wider text-stone-500 block mb-1">Finger Configuration Binding Layer</label>

                    {% for pat_key, label in labels.items() %}
                    <div class="flex items-center justify-between gap-3 bg-[#161413]/60 p-2 rounded-xl border border-[#2c2724]/80">
                        <span class="text-xs font-sans text-stone-300 font-medium truncate max-w-[170px]">{{ label }}</span>
                        <select id="select-pattern-{{ pat_key }}" class="gesture-select-menu bg-[#161413] border border-[#322d2a] text-[11px] text-orange-400 font-mono rounded-lg px-1.5 py-1 focus:outline-none focus:border-orange-500/40 cursor-pointer max-w-[150px]">
                        </select>
                    </div>
                    {% endfor %}
                </div>

                <div class="grid grid-cols-2 gap-3 pt-3 border-t border-[#161413] shrink-0">
                    <button onclick="activateProfile()" class="py-2 px-3 bg-stone-800 hover:bg-stone-700 text-stone-100 font-bold rounded-xl text-xs shadow-md transition-all cursor-pointer border border-stone-700/30">Set Active</button>
                    <button onclick="saveProfileModifications()" class="py-2 px-3 bg-orange-500/10 hover:bg-orange-500/20 text-orange-300 font-bold border border-orange-500/20 rounded-xl text-xs transition-all cursor-pointer">Save Changes</button>
                </div>

                <div class="grid grid-cols-2 gap-3 pt-1 shrink-0">
                    <button id="toggle-face-btn" onclick="toggleFaceEngine()" class="w-full py-2 px-4 bg-stone-900 text-stone-400 font-medium rounded-xl text-xs">Loading...</button>
                    <button id="toggle-camera-btn" onclick="toggleCameraEngine()" class="w-full py-2 px-4 bg-stone-900 text-stone-400 font-medium rounded-xl text-xs">Loading...</button>
                </div>
            </div>
        </div>
    </main>

    <style>
        .custom-scrollbar::-webkit-scrollbar {
            width: 5px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
            background: rgba(22, 20, 19, 0.5); 
            border-radius: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
            background: rgba(120, 113, 108, 0.3); 
            border-radius: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
            background: rgba(251, 146, 60, 0.4); 
        }
    </style>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML, labels=FINGER_LABELS)


def generate_web_stream():
    for frame in generate_frames():
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(generate_web_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/state')
def get_state():
    return jsonify(STATE)


@app.route('/api/logs')
def get_logs():
    return jsonify(SYSTEM_LOGS)


@app.route('/api/profiles')
def get_profiles():
    return jsonify(PROFILES)


@app.route('/api/hooks')
def get_hooks():
    return jsonify(AVAILABLE_COMMAND_HOOKS)


@app.route('/api/activate_profile', methods=['POST'])
def activate_profile():
    data = request.get_json()
    if data and "key" in data:
        key = data["key"]
        if key in PROFILES:
            STATE["active_profile_key"] = key
            STATE["current_user"] = PROFILES[key]["name"]
            return jsonify({"success": True})
    return jsonify({"error": "Bad slot lookup parameters"}), 400


@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    data = request.get_json()
    if data and "key" in data and "name" in data and "gestures" in data:
        key = data["key"]
        if key in PROFILES:
            PROFILES[key]["name"] = str(data["name"])
            PROFILES[key]["gestures"] = data["gestures"]
            save_profiles()
            if STATE["active_profile_key"] == key:
                STATE["current_user"] = PROFILES[key]["name"]
            return jsonify({"success": True})
    return jsonify({"error": "Missing profile updating metrics"}), 400


@app.route('/api/create_custom_command', methods=['POST'])
def create_custom_command():
    data = request.get_json()
    if data and all(k in data for k in ["key", "label", "type", "target"]):
        key = data["key"]
        if key in PROFILES:
            if "custom_commands" not in PROFILES[key]:
                PROFILES[key]["custom_commands"] = {}

            PROFILES[key]["custom_commands"][data["label"]] = {
                "type": data["type"],
                "target": data["target"]
            }
            save_profiles()
            return jsonify({"success": True})
    return jsonify({"error": "Invalid action creator specifications"}), 400


@app.route('/api/delete_custom_command', methods=['POST'])
def delete_custom_command():
    data = request.get_json()
    if data and "key" in data and "label" in data:
        key = data["key"]
        lbl = data["label"]
        if key in PROFILES and "custom_commands" in PROFILES[key]:
            if lbl in PROFILES[key]["custom_commands"]:
                del PROFILES[key]["custom_commands"][lbl]

                # Auto-scrub references to this action out of the gesture map
                for pat in list(PROFILES[key]["gestures"].keys()):
                    if PROFILES[key]["gestures"][pat] == lbl:
                        PROFILES[key]["gestures"][pat] = ""

                save_profiles()
                return jsonify({"success": True})
    return jsonify({"error": "Skins file delete failure"}), 400


@app.route('/api/toggle_face', methods=['POST'])
def toggle_face():
    STATE["face_recognition_enabled"] = not STATE["face_recognition_enabled"]
    return jsonify({"success": True, "new_state": STATE["face_recognition_enabled"]})


@app.route('/api/toggle_camera', methods=['POST'])
def toggle_camera():
    STATE["camera_enabled"] = not STATE.get("camera_enabled", True)
    return jsonify({"success": True, "new_state": STATE["camera_enabled"]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
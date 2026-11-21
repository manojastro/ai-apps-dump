(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const startBtn = $("start");
  const endBtn = $("end");
  const statusEl = $("status");
  const codeEl = $("code");
  const joinUrlEl = $("joinUrl");
  const copyBtn = $("copyLink");
  const sessionSec = $("session");
  const agentNameInput = $("agentName");
  const canvas = $("screen");
  const ctx = canvas.getContext("2d");
  const statsEl = $("stats");
  let framesInWindow = 0;
  let bytesInWindow = 0;
  let lastFrameAt = 0;
  setInterval(() => {
    const fps = framesInWindow;
    const kbps = Math.round((bytesInWindow * 8) / 1000);
    statsEl.textContent = "FPS: " + fps + " · kbps: " + kbps;
    framesInWindow = 0;
    bytesInWindow = 0;
  }, 1000);
  const uacBanner = $("uacBanner");
  const elevInteractive = $("elevInteractive");
  const credForm = $("credForm");
  const credDomain = $("credDomain");
  const credUser = $("credUser");
  const credPass = $("credPass");
  const elevStatus = $("elevStatus");
  const runBtn = $("runScript");

  let ws = null;
  let code = null;
  let connected = false;

  function setStatus(s) { statusEl.textContent = s; }

  function wsUrl() {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    return proto + "//" + location.host + "/ws";
  }

  function joinLink(c) {
    // Path-style link, easier to read aloud. Uses current host (works locally + prod).
    const scheme = location.protocol === "https:" ? "https:" : location.protocol;
    return scheme + "//" + location.host + "/j/" + c;
  }

  function connect() {
    return new Promise((resolve, reject) => {
      const sock = new WebSocket(wsUrl());
      sock.binaryType = "arraybuffer";
      const timer = setTimeout(() => { try { sock.close(); } catch {} reject(new Error("ws timeout")); }, 8000);
      sock.onopen = () => { clearTimeout(timer); resolve(sock); };
      sock.onerror = () => { clearTimeout(timer); reject(new Error("ws error")); };
    });
  }

  function send(obj) {
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj));
  }

  function setConnectedUI(on) {
    connected = on;
    elevInteractive.disabled = !on;
    credForm.querySelector("button[type=submit]").disabled = !on;
    runBtn.disabled = true; // Phase 6 enables when active; keep disabled in Phase 1
    if (on) runBtn.disabled = false;
    for (const id of ["keyWin", "keyAltTab", "keyCtrlEsc", "keyPrtScn"]) {
      $(id).disabled = !on;
    }
    // Ctrl+Alt+Del stays disabled until Phase 5 elevation succeeds; any
    // disconnect revokes it.
    if (!on) $("keyCAD").disabled = true;
  }

  startBtn.onclick = async () => {
    setStatus("Connecting…");
    startBtn.disabled = true;
    try {
      ws = await connect();
    } catch (e) {
      setStatus("Could not connect to server.");
      startBtn.disabled = false;
      return;
    }
    const agentName = (agentNameInput.value || "Agent").slice(0, 64);
    ws.onmessage = onMessage;
    ws.onclose = () => {
      setStatus("Disconnected.");
      startBtn.disabled = false;
      setConnectedUI(false);
    };
    send({ t: "agent.create", agentName });
    setStatus("Creating session…");
  };

  function onMessage(ev) {
    if (typeof ev.data !== "string") {
      onBinaryFrame(ev.data);
      return;
    }
    let msg;
    try { msg = JSON.parse(ev.data); } catch { return; }
    if (!msg || typeof msg.t !== "string") return;
    switch (msg.t) {
      case "session.created": {
        code = String(msg.code || "");
        codeEl.textContent = code;
        const link = joinLink(code);
        joinUrlEl.textContent = link;
        joinUrlEl.href = link;
        sessionSec.hidden = false;
        setStatus("Waiting for user… (share the code + link)");
        setConnectedUI(false);
        break;
      }
      case "peer.joined": {
        setStatus("Awaiting consent…");
        break;
      }
      case "consent.result": {
        if (msg.accepted === true) {
          setStatus("Connected");
          setConnectedUI(true);
        } else {
          setStatus("User declined.");
          setConnectedUI(false);
        }
        break;
      }
      case "peer.left": {
        setStatus("Peer left.");
        setConnectedUI(false);
        break;
      }
      case "host.elevated": {
        if (msg.ok === true) {
          elevStatus.textContent = "Elevated — UAC prompts unlocked.";
          $("keyCAD").disabled = false;
        } else {
          elevStatus.textContent = "Elevation failed: " + String(msg.error || "unknown");
        }
        break;
      }
      case "host.desktopChanged": {
        if (msg.desktop === "Winlogon") uacBanner.hidden = false;
        else uacBanner.hidden = true;
        break;
      }
      case "error": {
        setStatus("Error: " + String(msg.error || "unknown"));
        if (String(msg.error || "") === "tls_required") elevStatus.textContent = "Elevation refused: TLS required.";
        break;
      }
      default:
        break;
    }
  }

  endBtn.onclick = () => {
    try { send({ t: "agent.end" }); } catch {}
    try { ws && ws.close(); } catch {}
    setStatus("Ended.");
    setConnectedUI(false);
    startBtn.disabled = false;
  };

  copyBtn.onclick = async () => {
    try { await navigator.clipboard.writeText(joinUrlEl.textContent || ""); } catch {}
  };

  elevInteractive.onclick = () => {
    send({ t: "agent.requestElevation", mode: "interactive" });
    elevStatus.textContent = "Asked the user to approve the Windows prompt on their screen.";
  };
  $("keyCAD").onclick = () => {
    send({ t: "agent.sas" });
  };

  credForm.onsubmit = (e) => {
    e.preventDefault();
    // Never persist credentials. Send once, then clear immediately.
    const payload = {
      t: "agent.requestElevation",
      mode: "credential",
      domain: credDomain.value,
      username: credUser.value,
      password: credPass.value,
    };
    send(payload);
    credDomain.value = "";
    credUser.value = "";
    credPass.value = "";
    elevStatus.textContent = "Credentials sent (fields cleared).";
  };

  // Phase 3: binary video frames. [0x01][jpeg] full frame,
  // [0x02][x:u16be][y:u16be][w:u16be][h:u16be][jpeg] dirty rect.
  // Canvas backing store stays at native remote resolution (exact input mapping).
  async function onBinaryFrame(data) {
    let buf;
    if (data instanceof ArrayBuffer) buf = new Uint8Array(data);
    else if (data instanceof Blob) buf = new Uint8Array(await data.arrayBuffer());
    else return;
    if (buf.length < 2) return;
    const type = buf[0];
    try {
      if (type === 0x01) {
        const bmp = await createImageBitmap(new Blob([buf.slice(1)], { type: "image/jpeg" }));
        if (canvas.width !== bmp.width || canvas.height !== bmp.height) {
          canvas.width = bmp.width;
          canvas.height = bmp.height;
        }
        ctx.drawImage(bmp, 0, 0);
        bmp.close();
        framesInWindow++;
        bytesInWindow += buf.length;
        lastFrameAt = performance.now();
      } else if (type === 0x02 && buf.length > 9) {
        const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
        const x = dv.getUint16(1), y = dv.getUint16(3), w = dv.getUint16(5), h = dv.getUint16(7);
        const bmp = await createImageBitmap(new Blob([buf.slice(9)], { type: "image/jpeg" }));
        ctx.drawImage(bmp, x, y, w, h);
        bmp.close();
        framesInWindow++;
        bytesInWindow += buf.length;
        lastFrameAt = performance.now();
      }
    } catch {}
  }

  // ---- Phase 4: remote input ----
  function sendInput(obj) {
    if (connected) send(Object.assign({ t: "agent.input" }, obj));
  }
  // Canvas CSS size != backing store: map via the backing-store ratio so the
  // remote cursor lands exactly (critical on multi-monitor virtual desktops).
  function canvasPos(ev) {
    const r = canvas.getBoundingClientRect();
    const sx = canvas.width / Math.max(1, r.width);
    const sy = canvas.height / Math.max(1, r.height);
    return {
      x: Math.max(0, Math.round((ev.clientX - r.left) * sx)),
      y: Math.max(0, Math.round((ev.clientY - r.top) * sy)),
    };
  }
  function buttonName(b) {
    return b === 1 ? "middle" : b === 2 ? "right" : "left";
  }
  let lastMoveAt = 0;
  canvas.addEventListener("mousemove", (ev) => {
    const now = performance.now();
    if (now - lastMoveAt < 16) return; // throttle to ~60/s
    lastMoveAt = now;
    const p = canvasPos(ev);
    sendInput({ kind: "mouse-move", x: p.x, y: p.y });
  });
  canvas.addEventListener("mousedown", (ev) => {
    try { canvas.focus(); } catch {}
    const p = canvasPos(ev);
    sendInput({ kind: "mouse-down", button: buttonName(ev.button), x: p.x, y: p.y });
    ev.preventDefault();
  });
  canvas.addEventListener("mouseup", (ev) => {
    const p = canvasPos(ev);
    sendInput({ kind: "mouse-up", button: buttonName(ev.button), x: p.x, y: p.y });
    ev.preventDefault();
  });
  canvas.addEventListener("wheel", (ev) => {
    const p = canvasPos(ev);
    sendInput({ kind: "wheel", dx: Math.round(ev.deltaX), dy: Math.round(ev.deltaY), x: p.x, y: p.y });
    ev.preventDefault();
  }, { passive: false });
  // The two click pairs already went out as down/up; dblclick only needs
  // suppression so the browser doesn't start text selection etc.
  canvas.addEventListener("dblclick", (ev) => ev.preventDefault());
  // Suppress the browser's own menu; right-click arrives as button 2 down/up.
  canvas.addEventListener("contextmenu", (ev) => ev.preventDefault());
  canvas.addEventListener("keydown", (ev) => {
    sendInput({ kind: "key-down", code: ev.code });
    // Keep Tab/arrows/space etc. from escaping the remote session.
    if (connected) ev.preventDefault();
  });
  canvas.addEventListener("keyup", (ev) => {
    sendInput({ kind: "key-up", code: ev.code });
    if (connected) ev.preventDefault();
  });
  function tap(code) {
    sendInput({ kind: "key-down", code });
    sendInput({ kind: "key-up", code });
  }
  $("keyWin").onclick = () => tap("MetaLeft");
  $("keyPrtScn").onclick = () => tap("PrintScreen");
  $("keyAltTab").onclick = () => {
    sendInput({ kind: "key-down", code: "AltLeft" });
    tap("Tab");
    sendInput({ kind: "key-up", code: "AltLeft" });
  };
  $("keyCtrlEsc").onclick = () => {
    sendInput({ kind: "key-down", code: "ControlLeft" });
    tap("Escape");
    sendInput({ kind: "key-up", code: "ControlLeft" });
  };

  // Phase 3 rendering placeholder: keep 2d context to prove canvas wiring.
  try { void ctx; void lastFrameAt; } catch {}
})();

/* Utah Flux Studio — visual Lego IDE (no CLI required) */

const state = {
  bricks: [],
  links: [],
  catalog: [],
  selectedId: null,
  linkFrom: null,
  compiled: null,
  serialPort: null,
  serialReader: null,
  playing: false,
  wireCache: {},
};

const canvas = document.getElementById("canvas");
const brickLayer = document.getElementById("brickLayer");
const wireLayer = document.getElementById("wireLayer");
const palette = document.getElementById("brickPalette");
const templateList = document.getElementById("templateList");
const logPanel = document.getElementById("logPanel");
const emptyHint = document.getElementById("emptyHint");

function log(msg, level = "info") {
  const line = document.createElement("div");
  line.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
  if (level === "error") line.style.color = "#ff8f8f";
  if (level === "ok") line.style.color = "#9effcf";
  logPanel.appendChild(line);
  logPanel.scrollTop = logPanel.scrollHeight;
}

function uid() {
  return "b" + Math.random().toString(36).slice(2, 9);
}

function projectPayload() {
  return {
    version: 1,
    name: document.getElementById("projectName").value.trim() || "My Project",
    bricks: state.bricks,
    links: state.links,
  };
}

async function loadCatalog() {
  const res = await fetch("/api/bricks");
  const data = await res.json();
  state.catalog = data.bricks || [];
  renderPalette();
}

async function loadTemplates() {
  const res = await fetch("/api/templates");
  const data = await res.json();
  templateList.innerHTML = "";
  (data.templates || []).forEach((t) => {
    const btn = document.createElement("button");
    btn.className = "template-item";
    btn.textContent = `${t.emoji} ${t.name}`;
    btn.title = t.description;
    btn.onclick = () => loadTemplate(t.id);
    templateList.appendChild(btn);
  });
}

async function loadTemplate(id) {
  const res = await fetch(`/api/templates/${id}`);
  const data = await res.json();
  if (!data.project) return;
  applyProject(data.project);
  log(`Loaded template: ${data.project.name}`, "ok");
}

function applyProject(project) {
  state.bricks = project.bricks || [];
  state.links = project.links || [];
  document.getElementById("projectName").value = project.name || "My Project";
  state.selectedId = null;
  renderBoard();
}

function renderPalette() {
  palette.innerHTML = "";
  const groups = { trigger: [], action: [], sensor: [], logic: [] };
  state.catalog.forEach((b) => groups[b.category]?.push(b));

  Object.entries(groups).forEach(([cat, items]) => {
    if (!items.length) return;
    const title = document.createElement("div");
    title.className = "hint";
    title.textContent = cat.charAt(0).toUpperCase() + cat.slice(1) + "s";
    palette.appendChild(title);
    items.forEach((b) => {
      const el = document.createElement("div");
      el.className = "palette-brick";
      el.style.background = b.color;
      el.draggable = true;
      el.dataset.type = b.id;
      el.innerHTML = `<span>${b.emoji}</span><span>${b.label}</span>`;
      el.addEventListener("dragstart", (ev) => {
        ev.dataTransfer.setData("brickType", b.id);
      });
      palette.appendChild(el);
    });
  });
}

function defaultParams(brickType) {
  const spec = state.catalog.find((b) => b.id === brickType);
  if (!spec) return {};
  const params = {};
  Object.entries(spec.params || {}).forEach(([key, meta]) => {
    params[key] = meta.default;
  });
  return params;
}

canvas.addEventListener("dragover", (e) => e.preventDefault());
canvas.addEventListener("drop", (e) => {
  e.preventDefault();
  const type = e.dataTransfer.getData("brickType");
  if (!type) return;
  const rect = canvas.getBoundingClientRect();
  const brick = {
    id: uid(),
    type,
    x: Math.max(10, e.clientX - rect.left - 100),
    y: Math.max(10, e.clientY - rect.top - 36),
    params: defaultParams(type),
  };
  state.bricks.push(brick);
  renderBoard();
  log(`Added brick: ${type}`);
});

function renderBoard() {
  brickLayer.innerHTML = "";
  emptyHint.style.display = state.bricks.length ? "none" : "block";
  state.bricks.forEach((b) => {
    const spec = state.catalog.find((c) => c.id === b.type) || { label: b.type, emoji: "🧱", color: "#607D8B" };
    const el = document.createElement("div");
    el.className = "board-brick" + (state.selectedId === b.id ? " selected" : "");
    el.style.left = `${b.x}px`;
    el.style.top = `${b.y}px`;
    el.style.background = spec.color;
    el.dataset.id = b.id;
    el.innerHTML = `
      <div class="title"><span>${spec.emoji}</span><span>${spec.label}</span></div>
      <div class="sub">${spec.description || ""}</div>
      <div class="socket socket-out" data-socket="out" title="Drag wire from here"></div>
      <div class="socket socket-in" data-socket="in" title="Connect wire here"></div>
    `;

    enableDrag(el, b);
    el.addEventListener("click", (ev) => {
      if (ev.target.dataset.socket) return;
      state.selectedId = b.id;
      renderBoard();
      renderInspector();
    });

    el.querySelector('[data-socket="out"]').addEventListener("click", (ev) => {
      ev.stopPropagation();
      state.linkFrom = b.id;
      log("Pick another brick input dot to connect");
    });
    el.querySelector('[data-socket="in"]').addEventListener("click", (ev) => {
      ev.stopPropagation();
      if (!state.linkFrom || state.linkFrom === b.id) return;
      if (!state.links.some((l) => l.from === state.linkFrom && l.to === b.id)) {
        state.links.push({ from: state.linkFrom, to: b.id });
        log("Connected bricks", "ok");
      }
      state.linkFrom = null;
      renderBoard();
    });

    brickLayer.appendChild(el);
  });
  drawWires();
}

function drawWires() {
  wireLayer.innerHTML = "";
  state.links.forEach((link) => {
    const fromEl = brickLayer.querySelector(`[data-id="${link.from}"]`);
    const toEl = brickLayer.querySelector(`[data-id="${link.to}"]`);
    if (!fromEl || !toEl) return;
    const x1 = fromEl.offsetLeft + fromEl.offsetWidth;
    const y1 = fromEl.offsetTop + fromEl.offsetHeight / 2;
    const x2 = toEl.offsetLeft;
    const y2 = toEl.offsetTop + toEl.offsetHeight / 2;
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    const cx = (x1 + x2) / 2;
    path.setAttribute("d", `M ${x1} ${y1} C ${cx} ${y1}, ${cx} ${y2}, ${x2} ${y2}`);
    path.setAttribute("stroke", "#5b7cfa");
    path.setAttribute("stroke-width", "4");
    path.setAttribute("fill", "none");
    path.setAttribute("stroke-linecap", "round");
    wireLayer.appendChild(path);
  });
}

function enableDrag(el, brick) {
  let startX = 0;
  let startY = 0;
  let originX = 0;
  let originY = 0;
  el.addEventListener("pointerdown", (ev) => {
    if (ev.target.dataset.socket) return;
    startX = ev.clientX;
    startY = ev.clientY;
    originX = brick.x;
    originY = brick.y;
    el.setPointerCapture(ev.pointerId);
  });
  el.addEventListener("pointermove", (ev) => {
    if (!el.hasPointerCapture(ev.pointerId)) return;
    brick.x = Math.max(0, originX + (ev.clientX - startX));
    brick.y = Math.max(0, originY + (ev.clientY - startY));
    el.style.left = `${brick.x}px`;
    el.style.top = `${brick.y}px`;
    drawWires();
  });
  el.addEventListener("pointerup", (ev) => {
    if (el.hasPointerCapture(ev.pointerId)) el.releasePointerCapture(ev.pointerId);
  });
}

function renderInspector() {
  const body = document.getElementById("inspectorBody");
  const brick = state.bricks.find((b) => b.id === state.selectedId);
  if (!brick) {
    body.innerHTML = '<p class="hint">Click a brick on the board to change its settings.</p>';
    return;
  }
  const spec = state.catalog.find((c) => c.id === brick.type);
  body.innerHTML = `<p><strong>${spec?.emoji || ""} ${spec?.label || brick.type}</strong></p>`;
  const params = spec?.params || {};
  Object.entries(params).forEach(([key, meta]) => {
    const wrap = document.createElement("label");
    wrap.textContent = meta.label || key;
    let input;
    if (meta.type === "choice") {
      input = document.createElement("select");
      (meta.choices || []).forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c;
        opt.textContent = c;
        if (brick.params[key] === c) opt.selected = true;
        input.appendChild(opt);
      });
    } else if (meta.type === "number") {
      input = document.createElement("input");
      input.type = "number";
      input.min = meta.min;
      input.max = meta.max;
      input.step = 0.1;
      input.value = brick.params[key] ?? meta.default;
    } else {
      input = document.createElement("input");
      input.type = "text";
      input.value = brick.params[key] ?? meta.default ?? "";
    }
    input.addEventListener("change", () => {
      brick.params[key] = meta.type === "number" ? Number(input.value) : input.value;
      renderBoard();
    });
    wrap.appendChild(input);
    body.appendChild(wrap);
  });
  const del = document.createElement("button");
  del.className = "btn btn-gray btn-small";
  del.textContent = "🗑 Remove Brick";
  del.onclick = () => {
    state.bricks = state.bricks.filter((b) => b.id !== brick.id);
    state.links = state.links.filter((l) => l.from !== brick.id && l.to !== brick.id);
    state.selectedId = null;
    renderBoard();
    renderInspector();
  };
  body.appendChild(del);
}

async function compileProject() {
  const res = await fetch("/api/compile", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project: projectPayload() }),
  });
  const data = await res.json();
  const chip = document.getElementById("compileChip");
  if (!data.ok) {
    chip.textContent = "Needs fixes";
    chip.className = "chip chip-bad";
    log((data.errors || ["Compile failed"]).join("; "), "error");
    return null;
  }
  chip.textContent = "Ready to play";
  chip.className = "chip chip-ok";
  state.compiled = data;
  return data;
}

async function injectIntent(intent) {
  if (!state.serialPort?.writable) throw new Error("Connect your device first");
  const writer = state.serialPort.writable.getWriter();
  await writer.write(new TextEncoder().encode(JSON.stringify(intent) + "\n"));
  writer.releaseLock();
}

function applyWireTransforms(telemetry, wires) {
  const patch = {};
  wires.forEach((wire) => {
    const value = readPath(telemetry, wire.source);
    if (value == null) return;
    const mapped = transformWire(wire, value);
    writePath(patch, wire.sink, mapped);
  });
  return patch;
}

function readPath(obj, key) {
  if (!key.includes(".")) return obj[key];
  return key.split(".").reduce((acc, part) => (acc && acc[part] != null ? acc[part] : null), obj);
}

function writePath(obj, path, value) {
  const parts = Array.isArray(path) ? path : [];
  let node = obj;
  for (let i = 0; i < parts.length - 1; i++) {
    node[parts[i]] = node[parts[i]] || {};
    node = node[parts[i]];
  }
  node[parts[parts.length - 1]] = value;
}

function transformWire(wire, value) {
  const p = wire.params || {};
  if (wire.transform === "const_true") return true;
  if (wire.transform === "const_duration") return p.length === "long" ? 200 : 80;
  if (wire.transform === "tilt_message") return `${p.text || "Tilt"} (${Number(value).toFixed(2)})`;
  if (wire.transform === "tilt_pitch") {
    const base = { low: 300, medium: 660, high: 1200 }[p.pitch || "medium"];
    return Math.min(1800, Math.max(220, base + Math.abs(Number(value)) * 200));
  }
  return value;
}

async function readSerialLoop() {
  if (!state.serialPort?.readable) return;
  const decoder = new TextDecoderStream();
  state.serialPort.readable.pipeTo(decoder.writable);
  state.serialReader = decoder.readable.getReader();
  while (state.playing) {
    const { value, done } = await state.serialReader.read();
    if (done) break;
    if (!value) continue;
    value.split("\n").forEach(async (line) => {
      line = line.trim();
      if (!line.startsWith("{")) return;
      try {
        const frame = JSON.parse(line);
        if (frame.type === "telemetry" && state.compiled?.wires?.length) {
          const patch = applyWireTransforms(frame, state.compiled.wires);
          if (Object.keys(patch).length) await injectIntent(patch);
        }
      } catch (_) {}
    });
  }
}

document.getElementById("btnConnect").onclick = async () => {
  if (!("serial" in navigator)) {
    log("Use Chrome or Edge for USB device connect", "error");
    return;
  }
  try {
    state.serialPort = await navigator.serial.requestPort();
    await state.serialPort.open({ baudRate: 115200 });
    document.getElementById("statusChip").textContent = "Device: Connected";
    document.getElementById("statusChip").className = "chip chip-on";
    log("Device connected", "ok");
  } catch (e) {
    log(String(e), "error");
  }
};

document.getElementById("btnPlay").onclick = async () => {
  const compiled = await compileProject();
  if (!compiled) return;
  try {
    await injectIntent(compiled.intent);
    state.playing = true;
    readSerialLoop();
    log("Project is running on device", "ok");
  } catch (e) {
    log(String(e), "error");
  }
};

document.getElementById("btnStop").onclick = async () => {
  state.playing = false;
  try {
    if (state.serialReader) {
      await state.serialReader.cancel();
      state.serialReader = null;
    }
    await injectIntent({ speaker: { stop: true } });
    log("Stopped", "ok");
  } catch (e) {
    log(String(e), "error");
  }
};

document.getElementById("btnSave").onclick = () => {
  const blob = new Blob([JSON.stringify(projectPayload(), null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = (document.getElementById("projectName").value || "project").replace(/\s+/g, "_") + ".flux.json";
  a.click();
  log("Project saved to your computer", "ok");
};

document.getElementById("btnLoad").onclick = () => document.getElementById("fileInput").click();
document.getElementById("fileInput").onchange = async (ev) => {
  const file = ev.target.files?.[0];
  if (!file) return;
  const text = await file.text();
  applyProject(JSON.parse(text));
  log(`Opened ${file.name}`, "ok");
};

loadCatalog();
loadTemplates();
renderBoard();

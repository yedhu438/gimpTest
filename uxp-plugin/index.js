// index.js — Varsany UXP Plugin
// ================================
// Runs inside Photoshop 2026+ as a UXP panel plugin.
// Uses setInterval to poll the jobs folder every 3 seconds — non-blocking,
// Photoshop UI stays fully responsive at all times.

const { app, core, action, constants } = require("photoshop");
const uxp = require("uxp");
const fs = uxp.storage.localFileSystem;

const POLL_MS     = 3000;
const JOBS_PATH   = "C:\\Varsany\\photoshop_bridge\\jobs";
const DONE_PATH   = "C:\\Varsany\\photoshop_bridge\\done";
const ERROR_PATH  = "C:\\Varsany\\photoshop_bridge\\error";

let processing = false;

// ── UI elements ────────────────────────────────────────────────────────────────
const statusEl = document.getElementById("status");
const logEl    = document.getElementById("log");

function log(msg) {
    const d = new Date();
    const t = d.getHours()+":"+String(d.getMinutes()).padStart(2,"0")+":"+String(d.getSeconds()).padStart(2,"0");
    logEl.innerHTML = `[${t}] ${msg}` + "<br>" + logEl.innerHTML;
}

function setStatus(msg, color="#7ec87e") {
    statusEl.innerHTML = `<span class="dot" style="background:${color}"></span>${msg}`;
}

// ── Timestamp ──────────────────────────────────────────────────────────────────
function ts() {
    const d = new Date();
    const p = n => String(n).padStart(2,"0");
    return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

// ── File helpers ───────────────────────────────────────────────────────────────
async function getFolder(path) {
    try {
        return await fs.getEntryWithUrl("file:///" + path.replace(/\\/g, "/"));
    } catch(e) {
        return null;
    }
}

async function readJSON(entry) {
    const content = await entry.read({ format: uxp.storage.formats.utf8 });
    return JSON.parse(content);
}

async function writeJSON(folderPath, filename, data) {
    const folder = await getFolder(folderPath);
    if (!folder) return;
    const file = await folder.createFile(filename, { overwrite: true });
    await file.write(JSON.stringify(data, null, 2), { format: uxp.storage.formats.utf8 });
}

// ── Place customer image (uses Photoshop DOM API — ACE colour engine) ──────────
async function placeImage(doc, imagePath, layerName) {
    try {
        const layer = await doc.createLayer({ name: layerName });
        await action.batchPlay([{
            _obj: "placeEvent",
            null: { _path: imagePath, _kind: "local" },
            freeTransformCenterState: { _enum: "quadCenterState", _value: "QCSAverage" }
        }], { synchronousExecution: true });
        app.activeDocument.activeLayer.name = layerName;
        // Rasterize placed layer
        await action.batchPlay([{
            _obj: "rasterizeLayer",
            null: { _ref: [{ _enum: "ordinal", _value: "targetEnum", _ref: "layer" }] }
        }], { synchronousExecution: true });
        log("Placed image: " + layerName);
    } catch(e) {
        log("Image error: " + e.message);
    }
}

// ── Update text layer ──────────────────────────────────────────────────────────
async function setTextLayer(doc, layerName, lines, hex, fontName) {
    const layers = doc.layers;
    const layer  = findLayer(layers, layerName);
    if (!layer) { log("Layer not found: " + layerName); return; }

    const text = lines.join("\n");
    await core.executeAsModal(async () => {
        layer.textItem.contents = text;
        if (hex && hex.startsWith("#")) {
            const r = parseInt(hex.slice(1,3),16);
            const g = parseInt(hex.slice(3,5),16);
            const b = parseInt(hex.slice(5,7),16);
            layer.textItem.color = { red: r, green: g, blue: b };
        }
        if (fontName) {
            try { layer.textItem.font = fontName; } catch(e) {}
        }
    }, { commandName: "Set text layer" });
    log("Text set: " + layerName);
}

function findLayer(layers, name) {
    for (const l of layers) {
        if (l.name === name) return l;
        if (l.layers) {
            const found = findLayer(l.layers, name);
            if (found) return found;
        }
    }
    return null;
}

// ── Ensure output directory exists ────────────────────────────────────────────
async function ensureDir(filePath) {
    const parts = filePath.replace(/\\/g, "/").split("/");
    parts.pop(); // remove filename
    const dirPath = parts.join("/");
    try {
        await fs.getEntryWithUrl("file:///" + dirPath);
    } catch(e) {
        // Directory doesn't exist — create it
        try {
            const parentPath = parts.slice(0,-1).join("/");
            const parent = await fs.getEntryWithUrl("file:///" + parentPath);
            await parent.createFolder(parts[parts.length-1]);
        } catch(e2) {}
    }
}

// ── Process one job ────────────────────────────────────────────────────────────
async function processJob(jobEntry) {
    let job, orderId = jobEntry.name.replace(".json","");
    try {
        job     = await readJSON(jobEntry);
        orderId = job.order_id || orderId;
    } catch(e) {
        await writeJSON(ERROR_PATH, jobEntry.name, {
            order_id: orderId, error: "Parse error: "+e.message, failed_at: ts()
        });
        await jobEntry.delete();
        return;
    }

    log("Processing: " + orderId);
    setStatus("Processing: " + orderId, "#EF9F27");
    let doc = null;

    try {
        // Ensure output folder exists
        await ensureDir(job.output_path);

        // Open template using Photoshop DOM API — works in UXP, no restrictions
        const tplEntry = await fs.getEntryWithUrl("file:///" + job.template.replace(/\\/g,"/"));
        doc = await app.open(tplEntry);

        // Process zones
        for (const [zoneName, zone] of Object.entries(job.zones)) {
            log("Zone: " + zoneName);
            if (zone.customer_image) {
                await placeImage(doc, zone.customer_image, "CustomerImage_" + zoneName);
            }
            if (zone.text_lines && zone.text_lines.length > 0) {
                await setTextLayer(doc,
                    "CustomerText_" + zoneName,
                    zone.text_lines,
                    zone.colour_hex,
                    zone.font_name
                );
            }
        }

        // Save as PSD
        const outEntry = await fs.getEntryWithUrl("file:///" + job.output_path.replace(/\\/g,"/"));
        await doc.save(outEntry, {
            as: { _obj: "photoshop35Format" },
            embedProfiles: true
        });

        await doc.close(constants.SaveOptions.DONOTSAVECHANGES);
        doc = null;

        // Mark done
        await writeJSON(DONE_PATH, jobEntry.name, {
            order_id: orderId, output_path: job.output_path, completed_at: ts()
        });
        await jobEntry.delete();

        log("Done: " + orderId);
        setStatus("Watching for orders...");

    } catch(e) {
        if (doc) try { await doc.close(constants.SaveOptions.DONOTSAVECHANGES); } catch(x) {}
        await writeJSON(ERROR_PATH, jobEntry.name, {
            order_id: orderId, error: e.message || String(e), failed_at: ts()
        });
        try { await jobEntry.delete(); } catch(x) {}
        log("Error: " + orderId + " — " + e.message);
        setStatus("Error — see log", "#E24B4A");
    }
}

// ── Main poll loop — non-blocking setInterval ──────────────────────────────────
async function pollJobs() {
    if (processing) return;
    processing = true;
    try {
        const folder = await getFolder(JOBS_PATH);
        if (!folder) { processing = false; return; }
        const entries = await folder.getEntries();
        const jobs    = entries.filter(e => e.name.endsWith(".json")).sort((a,b) => a.name < b.name ? -1 : 1);
        if (jobs.length === 0) { processing = false; return; }
        log("Found " + jobs.length + " job(s)");
        // Process one job per tick — keeps UI responsive
        await processJob(jobs[0]);
    } catch(e) {
        log("Poll error: " + e.message);
    }
    processing = false;
}

// Start polling
setInterval(pollJobs, POLL_MS);
log("Varsany plugin started — polling every " + (POLL_MS/1000) + "s");

// ps_worker.jsx
// Varsany Automation — Headless Photoshop Worker
// ================================================
// Polls C:\Varsany\photoshop_bridge\jobs\ for JSON job files.
// ExtendScript (ES3) compatible — no JSON, no toISOString, no Array.forEach.

#target photoshop
app.bringToFront();

// ── Config ─────────────────────────────────────────────────────────────────────
var JOBS_DIR  = new Folder("C:/Varsany/photoshop_bridge/jobs");
var DONE_DIR  = new Folder("C:/Varsany/photoshop_bridge/done");
var ERROR_DIR = new Folder("C:/Varsany/photoshop_bridge/error");
var POLL_MS   = 2000;

// ── Timestamp (ES3 safe) ───────────────────────────────────────────────────────
function isoTimestamp() {
    var d = new Date();
    function pad(n) { return n < 10 ? "0" + n : "" + n; }
    return d.getFullYear() + "-" + pad(d.getMonth()+1) + "-" + pad(d.getDate()) +
           "T" + pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds());
}

// ── Logging ────────────────────────────────────────────────────────────────────
function log(msg) {
    $.writeln("[" + isoTimestamp() + "] " + msg);
}

// ── Simple JSON stringify (ES3 safe, handles our specific data structure) ───────
function simpleStringify(obj) {
    var out = "{\n";
    var first = true;
    for (var k in obj) {
        if (!obj.hasOwnProperty(k)) continue;
        if (!first) out += ",\n";
        first = false;
        var v = obj[k];
        if (v === null || v === undefined) {
            out += '  "' + k + '": null';
        } else if (typeof v === "string") {
            out += '  "' + k + '": "' + v.replace(/\\/g, "\\\\").replace(/"/g, '\\"') + '"';
        } else {
            out += '  "' + k + '": ' + v;
        }
    }
    out += "\n}";
    return out;
}

// ── Read JSON job file (eval is safe — files written by our own Python) ─────────
function readJSON(file) {
    file.encoding = "UTF-8";
    file.open("r");
    var content = file.read();
    file.close();
    return eval("(" + content + ")");
}

// ── Write result file ──────────────────────────────────────────────────────────
function writeResultFile(targetDir, filename, dataObj) {
    var outFile = new File(targetDir.fsName + "/" + filename);
    outFile.encoding = "UTF-8";
    outFile.open("w");
    outFile.write(simpleStringify(dataObj));
    outFile.close();
}

// ── Write error JSON and move job to error folder ──────────────────────────────
function writeError(jobFile, orderId, errorMsg) {
    log("ERROR on " + orderId + ": " + errorMsg);
    writeResultFile(ERROR_DIR, jobFile.name, {
        order_id:  orderId,
        error:     errorMsg,
        failed_at: isoTimestamp()
    });
    try { jobFile.remove(); } catch(e) {}
}

// ── Place customer image using Photoshop ACE colour engine ─────────────────────
function placeCustomerImage(doc, imagePath, layerName) {
    var f = new File(imagePath);
    if (!f.exists) {
        log("  Image not found: " + imagePath);
        return false;
    }
    var idPlc = charIDToTypeID("Plc ");
    var desc  = new ActionDescriptor();
    desc.putPath(charIDToTypeID("null"), f);
    desc.putEnumerated(charIDToTypeID("FTcs"), charIDToTypeID("QCSt"), charIDToTypeID("Qcsa"));
    executeAction(idPlc, desc, DialogModes.NO);

    var placed = doc.activeLayer;
    placed.name = layerName;

    // Rasterize smart object to pixel layer
    var idRstr = charIDToTypeID("Rstr");
    var descR  = new ActionDescriptor();
    descR.putEnumerated(charIDToTypeID("null"), charIDToTypeID("Ordn"), charIDToTypeID("Trgt"));
    executeAction(idRstr, descR, DialogModes.NO);
    return true;
}

// ── Update a named text layer ──────────────────────────────────────────────────
function setTextLayer(doc, layerName, textLines, colourHex, fontName) {
    var layer = findLayerByName(doc, layerName);
    if (!layer) {
        log("  Text layer '" + layerName + "' not found — skipping");
        return false;
    }
    if (layer.kind !== LayerKind.TEXT) {
        log("  Layer '" + layerName + "' is not a text layer — skipping");
        return false;
    }
    var ti = layer.textItem;
    // Join lines
    var joined = "";
    for (var i = 0; i < textLines.length; i++) {
        if (i > 0) joined += "\r";
        joined += textLines[i];
    }
    ti.contents = joined;
    // Set colour
    if (colourHex && colourHex.charAt(0) === "#") {
        var hex = colourHex.slice(1);
        var col = new SolidColor();
        col.rgb.red   = parseInt(hex.slice(0,2), 16);
        col.rgb.green = parseInt(hex.slice(2,4), 16);
        col.rgb.blue  = parseInt(hex.slice(4,6), 16);
        ti.color = col;
    }
    // Set font
    if (fontName) {
        try { ti.font = fontName; } catch(e) {
            log("  Font '" + fontName + "' not found — keeping template default");
        }
    }
    return true;
}

// ── Recursive layer search ─────────────────────────────────────────────────────
function findLayerByName(container, name) {
    var layers = container.layers;
    for (var i = 0; i < layers.length; i++) {
        var l = layers[i];
        if (l.name === name) return l;
        if (l.typename === "LayerSet") {
            var found = findLayerByName(l, name);
            if (found) return found;
        }
    }
    return null;
}

// ── Process one job ────────────────────────────────────────────────────────────
function processJob(jobFile) {
    var job = null;
    var orderId = jobFile.name;
    try {
        job = readJSON(jobFile);
        orderId = job.order_id;
    } catch(e) {
        writeError(jobFile, orderId, "Could not parse job JSON: " + e.message);
        return;
    }

    log("Processing: " + orderId);
    var doc = null;

    try {
        // 1. Open template PSD
        var templateFile = new File(job.template);
        if (!templateFile.exists) {
            throw new Error("Template not found: " + job.template);
        }
        doc = app.open(templateFile);

        // 2. Process zones — iterate keys manually (ES3)
        var zones = job.zones;
        var zoneNames = [];
        for (var z in zones) {
            if (zones.hasOwnProperty(z)) zoneNames.push(z);
        }
        for (var zi = 0; zi < zoneNames.length; zi++) {
            var zoneName = zoneNames[zi];
            var zone     = zones[zoneName];
            log("  Zone: " + zoneName);

            if (zone.customer_image) {
                placeCustomerImage(doc, zone.customer_image, "CustomerImage_" + zoneName);
            }
            if (zone.text_lines && zone.text_lines.length > 0) {
                setTextLayer(doc, "CustomerText_" + zoneName,
                             zone.text_lines, zone.colour_hex, zone.font_name);
            }
        }

        // 3. Save as layered PSD
        var outputFile  = new File(job.output_path);
        var saveOpts    = new PhotoshopSaveOptions();
        saveOpts.layers = true;
        saveOpts.embedColorProfile = true;
        doc.saveAs(outputFile, saveOpts, true);
        log("  Saved: " + job.output_path);

        // 4. Close document
        doc.close(SaveOptions.DONOTSAVECHANGES);
        doc = null;

        // 5. Write done file
        writeResultFile(DONE_DIR, jobFile.name, {
            order_id:     orderId,
            output_path:  job.output_path,
            completed_at: isoTimestamp()
        });
        jobFile.remove();
        log("Done: " + orderId);

    } catch(e) {
        try { if (doc) doc.close(SaveOptions.DONOTSAVECHANGES); } catch(ignored) {}
        writeError(jobFile, orderId, e.message || String(e));
    }
}

// ── Main poll loop ─────────────────────────────────────────────────────────────
log("Varsany PS Worker started.");
log("Watching: " + JOBS_DIR.fsName);
log("Poll interval: " + POLL_MS + "ms");

while (true) {
    var jobFiles = JOBS_DIR.getFiles("*.json");
    if (jobFiles.length > 0) {
        jobFiles.sort(function(a, b) {
            return a.name < b.name ? -1 : a.name > b.name ? 1 : 0;
        });
        processJob(jobFiles[0]);
    }
    $.sleep(POLL_MS);
}

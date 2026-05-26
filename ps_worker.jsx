// ps_worker.jsx
// Varsany Automation — Headless Photoshop Worker
// ================================================
// ONE-SHOT processor — processes all pending jobs in the jobs folder then exits.
// Python calls this script via subprocess for each batch, so Photoshop UI stays free.
// ExtendScript (ES3) compatible.

#target photoshop

// ── Config ─────────────────────────────────────────────────────────────────────
var JOBS_DIR  = new Folder("C:/Varsany/photoshop_bridge/jobs");
var DONE_DIR  = new Folder("C:/Varsany/photoshop_bridge/done");
var ERROR_DIR = new Folder("C:/Varsany/photoshop_bridge/error");

// ── Timestamp (ES3 safe) ───────────────────────────────────────────────────────
function isoTimestamp() {
    var d = new Date();
    function pad(n) { return n < 10 ? "0" + n : "" + n; }
    return d.getFullYear() + "-" + pad(d.getMonth()+1) + "-" + pad(d.getDate()) +
           "T" + pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds());
}

function log(msg) {
    $.writeln("[" + isoTimestamp() + "] " + msg);
}

// ── Simple JSON stringify (ES3 safe) ───────────────────────────────────────────
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
    return out + "\n}";
}

// ── Read JSON job file ─────────────────────────────────────────────────────────
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

// ── Write error and move job ───────────────────────────────────────────────────
function writeError(jobFile, orderId, errorMsg) {
    log("ERROR on " + orderId + ": " + errorMsg);
    writeResultFile(ERROR_DIR, jobFile.name, {
        order_id:  orderId,
        error:     errorMsg,
        failed_at: isoTimestamp()
    });
    try { jobFile.remove(); } catch(e) {}
}

// ── Place customer image ───────────────────────────────────────────────────────
function placeCustomerImage(doc, imagePath, layerName) {
    var f = new File(imagePath);
    if (!f.exists) { log("  Image not found: " + imagePath); return false; }
    var idPlc = charIDToTypeID("Plc ");
    var desc  = new ActionDescriptor();
    desc.putPath(charIDToTypeID("null"), f);
    desc.putEnumerated(charIDToTypeID("FTcs"), charIDToTypeID("QCSt"), charIDToTypeID("Qcsa"));
    executeAction(idPlc, desc, DialogModes.NO);
    var placed = doc.activeLayer;
    placed.name = layerName;
    var idRstr = charIDToTypeID("Rstr");
    var descR  = new ActionDescriptor();
    descR.putEnumerated(charIDToTypeID("null"), charIDToTypeID("Ordn"), charIDToTypeID("Trgt"));
    executeAction(idRstr, descR, DialogModes.NO);
    return true;
}

// ── Update text layer ──────────────────────────────────────────────────────────
function setTextLayer(doc, layerName, textLines, colourHex, fontName) {
    var layer = findLayerByName(doc, layerName);
    if (!layer) { log("  Text layer '" + layerName + "' not found"); return false; }
    if (layer.kind !== LayerKind.TEXT) { log("  '" + layerName + "' is not text"); return false; }
    var ti = layer.textItem;
    var joined = "";
    for (var i = 0; i < textLines.length; i++) {
        if (i > 0) joined += "\r";
        joined += textLines[i];
    }
    ti.contents = joined;
    if (colourHex && colourHex.charAt(0) === "#") {
        var hex = colourHex.slice(1);
        var col = new SolidColor();
        col.rgb.red   = parseInt(hex.slice(0,2), 16);
        col.rgb.green = parseInt(hex.slice(2,4), 16);
        col.rgb.blue  = parseInt(hex.slice(4,6), 16);
        ti.color = col;
    }
    if (fontName) {
        try { ti.font = fontName; } catch(e) {
            log("  Font '" + fontName + "' not found — keeping default");
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

// ── Process one job file ───────────────────────────────────────────────────────
function processJob(jobFile) {
    var job = null;
    var orderId = jobFile.name;
    try {
        job = readJSON(jobFile);
        orderId = job.order_id;
    } catch(e) {
        writeError(jobFile, orderId, "Cannot parse job: " + e.message);
        return;
    }
    log("Processing: " + orderId);
    var doc = null;
    try {
        var templateFile = new File(job.template);
        if (!templateFile.exists) throw new Error("Template not found: " + job.template);
        app.load(templateFile);
        doc = app.activeDocument;

        var zones = job.zones;
        for (var z in zones) {
            if (!zones.hasOwnProperty(z)) continue;
            var zone = zones[z];
            log("  Zone: " + z);
            if (zone.customer_image) {
                placeCustomerImage(doc, zone.customer_image, "CustomerImage_" + z);
            }
            if (zone.text_lines && zone.text_lines.length > 0) {
                setTextLayer(doc, "CustomerText_" + z, zone.text_lines, zone.colour_hex, zone.font_name);
            }
        }

        var outputFile  = new File(job.output_path);
        var saveOpts    = new PhotoshopSaveOptions();
        saveOpts.layers = true;
        saveOpts.embedColorProfile = true;
        doc.saveAs(outputFile, saveOpts, true);
        log("  Saved: " + job.output_path);
        doc.close(SaveOptions.DONOTSAVECHANGES);
        doc = null;

        writeResultFile(DONE_DIR, jobFile.name, {
            order_id:     orderId,
            output_path:  job.output_path,
            completed_at: isoTimestamp()
        });
        jobFile.remove();
        log("Done: " + orderId);

    } catch(e) {
        try { if (doc) doc.close(SaveOptions.DONOTSAVECHANGES); } catch(ig) {}
        writeError(jobFile, orderId, e.message || String(e));
    }
}

// ── ONE-SHOT: process all pending jobs then exit ───────────────────────────────
log("Varsany PS Worker — scanning jobs folder");
var jobFiles = JOBS_DIR.getFiles("*.json");
if (jobFiles.length === 0) {
    log("No pending jobs.");
} else {
    log("Found " + jobFiles.length + " job(s).");
    jobFiles.sort(function(a, b) { return a.name < b.name ? -1 : 1; });
    for (var ji = 0; ji < jobFiles.length; ji++) {
        processJob(jobFiles[ji]);
    }
}
log("Worker finished.");

// ps_worker.jsx
// Varsany Automation — Headless Photoshop Worker
// ================================================
// Polls W:\VarsaniAutomation\photoshop_bridge\jobs\ for JSON job files.
// For each job:
//   1. Opens the template PSD
//   2. Places customer image (Photoshop ACE handles ICC conversion automatically)
//   3. Updates text layers with customer personalisation
//   4. Saves layered PSD to output path
//   5. Moves job JSON to done\ or error\
//
// Run: Open Photoshop → File → Scripts → Browse → select this file
// Or launch via: Photoshop.exe ps_worker.jsx

#target photoshop
app.bringToFront();

// ── Config (mirror ps_bridge.py paths) ────────────────────────────────────────
var JOBS_DIR  = new Folder("C:/Varsany/photoshop_bridge/jobs");
var DONE_DIR  = new Folder("C:/Varsany/photoshop_bridge/done");
var ERROR_DIR = new Folder("C:/Varsany/photoshop_bridge/error");
var POLL_MS   = 2000;  // polling interval

// ── Logging ────────────────────────────────────────────────────────────────────
function log(msg) {
    $.writeln("[" + new Date().toLocaleTimeString() + "] " + msg);
}

// ── JSON reader (safe eval for internal files only) ────────────────────────────
function readJSON(file) {
    file.encoding = "UTF-8";
    file.open("r");
    var content = file.read();
    file.close();
    // Use eval with parentheses — safe because these files are written by our own Python
    return eval("(" + content + ")");
}

// ── Move a file to target folder ───────────────────────────────────────────────
function moveFile(srcFile, targetFolder) {
    var dest = new File(targetFolder.fsName + "/" + srcFile.name);
    if (dest.exists) dest.remove();
    srcFile.copy(dest);
    srcFile.remove();
}

// ── Write error result JSON ────────────────────────────────────────────────────
function writeError(jobFile, job, errorMsg) {
    log("ERROR on " + (job ? job.order_id : jobFile.name) + ": " + errorMsg);
    var result = {
        order_id:   job ? job.order_id : jobFile.name,
        error:      errorMsg,
        failed_at:  new Date().toISOString()
    };
    var outFile = new File(ERROR_DIR.fsName + "/" + jobFile.name);
    outFile.encoding = "UTF-8";
    outFile.open("w");
    outFile.write(JSON.stringify(result, null, 2));
    outFile.close();
    try { jobFile.remove(); } catch(e) {}
}

// ── Place a customer image into the document ───────────────────────────────────
// Uses "Place Embedded" which triggers Photoshop's ACE colour engine.
// The engine reads the source ICC profile and converts to the document
// colour profile automatically — this is the entire point of Option 2.
function placeCustomerImage(doc, imagePath, layerName) {
    var f = new File(imagePath);
    if (!f.exists) {
        log("  Image not found: " + imagePath);
        return false;
    }

    // Select Place Embedded (Photoshop CC+)
    var idPlc  = charIDToTypeID("Plc ");
    var desc   = new ActionDescriptor();
    desc.putPath(charIDToTypeID("null"), f);
    desc.putEnumerated(
        charIDToTypeID("FTcs"),
        charIDToTypeID("QCSt"),
        charIDToTypeID("Qcsa")   // centre in canvas
    );
    executeAction(idPlc, desc, DialogModes.NO);

    // The placed layer is now active — rename it and rasterize
    var placed = doc.activeLayer;
    placed.name = layerName;

    // Rasterize so it becomes a pixel layer (same as current Python output)
    var idRstr = charIDToTypeID("Rstr");
    var descR  = new ActionDescriptor();
    descR.putEnumerated(
        charIDToTypeID("null"),
        charIDToTypeID("Ordn"),
        charIDToTypeID("Trgt")
    );
    executeAction(idRstr, descR, DialogModes.NO);

    return true;
}

// ── Update a named text layer ──────────────────────────────────────────────────
function setTextLayer(doc, layerName, textLines, colourHex, fontName) {
    var layer = null;

    // Search all layers (including in groups) for the named text layer
    layer = findLayerByName(doc, layerName);
    if (!layer) {
        log("  Text layer '" + layerName + "' not found — skipping");
        return false;
    }
    if (layer.kind !== LayerKind.TEXT) {
        log("  Layer '" + layerName + "' is not a text layer — skipping");
        return false;
    }

    var ti = layer.textItem;

    // Set text content (join lines with newline)
    ti.contents = textLines.join("\r");

    // Set colour if provided
    if (colourHex && colourHex.charAt(0) === "#") {
        var hex = colourHex.slice(1);
        var r   = parseInt(hex.slice(0, 2), 16);
        var g   = parseInt(hex.slice(2, 4), 16);
        var b   = parseInt(hex.slice(4, 6), 16);
        var col = new SolidColor();
        col.rgb.red   = r;
        col.rgb.green = g;
        col.rgb.blue  = b;
        ti.color = col;
    }

    // Set font if provided (Photoshop postscript font name)
    if (fontName) {
        try { ti.font = fontName; } catch(e) {
            log("  Font '" + fontName + "' not available in Photoshop — keeping template default");
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
    try {
        job = readJSON(jobFile);
    } catch(e) {
        writeError(jobFile, null, "Could not parse job JSON: " + e.message);
        return;
    }

    log("Processing: " + job.order_id);

    var doc = null;
    try {
        // 1. Open template PSD
        var templateFile = new File(job.template);
        if (!templateFile.exists) {
            throw new Error("Template not found: " + job.template);
        }
        doc = app.open(templateFile);

        // 2. Process each zone (front / back / pocket / sleeve)
        var zones = job.zones;
        for (var zoneName in zones) {
            if (!zones.hasOwnProperty(zoneName)) continue;
            var zone = zones[zoneName];

            log("  Zone: " + zoneName);

            // Place customer image if provided
            if (zone.customer_image) {
                var imgLayerName = "CustomerImage_" + zoneName;
                placeCustomerImage(doc, zone.customer_image, imgLayerName);
            }

            // Update text layer if text provided
            if (zone.text_lines && zone.text_lines.length > 0) {
                var textLayerName = "CustomerText_" + zoneName;
                setTextLayer(
                    doc,
                    textLayerName,
                    zone.text_lines,
                    zone.colour_hex,
                    zone.font_name
                );
            }
        }

        // 3. Save as layered PSD
        var outputFile    = new File(job.output_path);
        var saveOpts      = new PhotoshopSaveOptions();
        saveOpts.layers   = true;   // keep layers — matches existing Python output format
        saveOpts.embedColorProfile = true;
        doc.saveAs(outputFile, saveOpts, true);

        log("  Saved: " + job.output_path);

        // 4. Close without saving changes again
        doc.close(SaveOptions.DONOTSAVECHANGES);
        doc = null;

        // 5. Mark done
        var doneData = {
            order_id:     job.order_id,
            output_path:  job.output_path,
            completed_at: new Date().toISOString()
        };
        var doneFile = new File(DONE_DIR.fsName + "/" + jobFile.name);
        doneFile.encoding = "UTF-8";
        doneFile.open("w");
        doneFile.write(JSON.stringify(doneData, null, 2));
        doneFile.close();
        jobFile.remove();

        log("Done: " + job.order_id);

    } catch(e) {
        // Close document if still open
        try { if (doc) doc.close(SaveOptions.DONOTSAVECHANGES); } catch(ignored) {}
        writeError(jobFile, job, e.message || String(e));
    }
}

// ── Main poll loop ─────────────────────────────────────────────────────────────
log("Varsany PS Worker started.");
log("Watching: " + JOBS_DIR.fsName);
log("Poll interval: " + POLL_MS + "ms");

while (true) {
    var jobFiles = JOBS_DIR.getFiles("*.json");

    if (jobFiles.length > 0) {
        // Sort by name (= order_id) so oldest submitted job runs first
        jobFiles.sort(function(a, b) {
            return a.name < b.name ? -1 : a.name > b.name ? 1 : 0;
        });
        processJob(jobFiles[0]);
    }

    $.sleep(POLL_MS);
}

// ps_worker.jsx  —  Varsany Automation
// ======================================
// Triggered by Python via Windows COM (win32com DoJavaScriptFile).
// Photoshop must already be open.
// Scans jobs folder, processes each job, exits.
// ES3 compatible (no JSON object, no Array.forEach, no toISOString).

#target photoshop

var JOBS_DIR  = new Folder("C:/Varsany/photoshop_bridge/jobs");
var DONE_DIR  = new Folder("C:/Varsany/photoshop_bridge/done");
var ERROR_DIR = new Folder("C:/Varsany/photoshop_bridge/error");

// ── Helpers ────────────────────────────────────────────────────────────────────
function ts() {
    var d = new Date();
    function p(n) { return n < 10 ? "0"+n : ""+n; }
    return d.getFullYear()+"-"+p(d.getMonth()+1)+"-"+p(d.getDate())
           +"T"+p(d.getHours())+":"+p(d.getMinutes())+":"+p(d.getSeconds());
}
function log(m) { $.writeln("["+ts()+"] "+m); }

function writeFile(folder, name, content) {
    var f = new File(folder.fsName+"/"+name);
    f.encoding = "UTF-8"; f.open("w"); f.write(content); f.close();
}

function readFile(f) {
    f.encoding = "UTF-8"; f.open("r");
    var s = f.read(); f.close(); return s;
}

function markDone(filename, orderId, outPath) {
    writeFile(DONE_DIR, filename,
        '{"order_id":"'+orderId+'","output_path":"'+outPath.replace(/\\/g,"\\\\")+
        '","completed_at":"'+ts()+'"}');
}

function markError(filename, orderId, msg) {
    msg = (""+msg).replace(/\\/g,"\\\\").replace(/"/g,'\\"').replace(/\n/g," ");
    writeFile(ERROR_DIR, filename,
        '{"order_id":"'+orderId+'","error":"'+msg+'","failed_at":"'+ts()+'"}');
}

// ── Layer helpers ──────────────────────────────────────────────────────────────
function findLayer(container, name) {
    var layers = container.layers;
    for (var i = 0; i < layers.length; i++) {
        if (layers[i].name === name) return layers[i];
        if (layers[i].typename === "LayerSet") {
            var found = findLayer(layers[i], name);
            if (found) return found;
        }
    }
    return null;
}

function placeImage(doc, imgPath, layerName) {
    var f = new File(imgPath);
    if (!f.exists) { log("  Image not found: "+imgPath); return; }
    // Place Embedded — ACE colour engine handles ICC conversion
    var d = new ActionDescriptor();
    d.putPath(charIDToTypeID("null"), f);
    d.putEnumerated(charIDToTypeID("FTcs"), charIDToTypeID("QCSt"), charIDToTypeID("Qcsa"));
    executeAction(charIDToTypeID("Plc "), d, DialogModes.NO);
    doc.activeLayer.name = layerName;
    // Rasterize
    var d2 = new ActionDescriptor();
    d2.putEnumerated(charIDToTypeID("null"), charIDToTypeID("Ordn"), charIDToTypeID("Trgt"));
    executeAction(charIDToTypeID("Rstr"), d2, DialogModes.NO);
}

function setText(doc, layerName, lines, hex, font) {
    var layer = findLayer(doc, layerName);
    if (!layer || layer.kind !== LayerKind.TEXT) {
        log("  Text layer '"+layerName+"' not found or not text"); return;
    }
    var ti = layer.textItem;
    var txt = "";
    for (var i = 0; i < lines.length; i++) { if (i>0) txt+="\r"; txt+=lines[i]; }
    ti.contents = txt;
    if (hex && hex.charAt(0)==="#") {
        var c = new SolidColor();
        c.rgb.red   = parseInt(hex.slice(1,3),16);
        c.rgb.green = parseInt(hex.slice(3,5),16);
        c.rgb.blue  = parseInt(hex.slice(5,7),16);
        ti.color = c;
    }
    if (font) { try { ti.font = font; } catch(e) { log("  Font '"+font+"' unavailable"); } }
}

// ── Process one job ────────────────────────────────────────────────────────────
function processJob(jobFile) {
    var orderId = jobFile.name.replace(".json","");
    var job;
    try {
        job = eval("("+readFile(jobFile)+")");
        orderId = job.order_id || orderId;
    } catch(e) {
        markError(jobFile.name, orderId, "Parse error: "+e.message);
        try { jobFile.remove(); } catch(x){}
        return;
    }

    log("Processing: "+orderId);
    var doc = null;
    try {
        // Open template
        var tpl = new File(job.template);
        if (!tpl.exists) throw new Error("Template not found: "+job.template);
        // Try multiple open methods for PS 2026 compatibility
        try {
            doc = app.open(tpl);
        } catch(e1) {
            try {
                app.load(tpl);
                doc = app.activeDocument;
            } catch(e2) {
                var dOpen = new ActionDescriptor();
                dOpen.putPath(charIDToTypeID("null"), tpl);
                executeAction(charIDToTypeID("Opn "), dOpen, DialogModes.NO);
                doc = app.activeDocument;
            }
        }

        // Process each zone
        var zones = job.zones;
        for (var z in zones) {
            if (!zones.hasOwnProperty(z)) continue;
            var zone = zones[z];
            log("  Zone: "+z);
            if (zone.customer_image) placeImage(doc, zone.customer_image, "CustomerImage_"+z);
            if (zone.text_lines && zone.text_lines.length > 0)
                setText(doc, "CustomerText_"+z, zone.text_lines, zone.colour_hex, zone.font_name);
        }

        // Save PSD
        var out = new File(job.output_path);
        var opts = new PhotoshopSaveOptions();
        opts.layers = true;
        opts.embedColorProfile = true;
        doc.saveAs(out, opts, true);
        log("  Saved: "+job.output_path);

        doc.close(SaveOptions.DONOTSAVECHANGES);
        doc = null;

        markDone(jobFile.name, orderId, job.output_path);
        try { jobFile.remove(); } catch(x){}
        log("Done: "+orderId);

    } catch(e) {
        try { if(doc) doc.close(SaveOptions.DONOTSAVECHANGES); } catch(x){}
        markError(jobFile.name, orderId, e.message || String(e));
        try { jobFile.remove(); } catch(x){}
        log("Error: "+orderId+" — "+e.message);
    }
}

// ── Run ────────────────────────────────────────────────────────────────────────
log("PS Worker start");
var jobs = JOBS_DIR.getFiles("*.json");
if (!jobs || jobs.length === 0) {
    log("No jobs.");
} else {
    log("Jobs found: "+jobs.length);
    jobs.sort(function(a,b){ return a.name < b.name ? -1 : 1; });
    for (var i = 0; i < jobs.length; i++) processJob(jobs[i]);
}
log("PS Worker done.");

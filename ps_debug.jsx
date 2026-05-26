// ps_debug.jsx — step by step debug for Photoshop 2026
#target photoshop

var JOBS_DIR = new Folder("C:/Varsany/photoshop_bridge/jobs");

alert("Step 1: Script started OK");

var jobs = JOBS_DIR.getFiles("*.json");
alert("Step 2: Found " + jobs.length + " job(s) in jobs folder");

if (jobs.length > 0) {
    var f = jobs[0];
    f.encoding = "UTF-8"; f.open("r");
    var content = f.read(); f.close();
    var job = eval("(" + content + ")");
    alert("Step 3: Job parsed OK\nOrder: " + job.order_id + "\nTemplate: " + job.template);

    var tpl = new File(job.template);
    alert("Step 4: Template file exists = " + tpl.exists + "\nPath: " + tpl.fsName);

    if (tpl.exists) {
        try {
            var doc = app.open(tpl);
            alert("Step 5: app.open() SUCCESS\nDoc: " + doc.name);
            doc.close(SaveOptions.DONOTSAVECHANGES);
        } catch(e) {
            alert("Step 5 FAILED: app.open() error:\n" + e.message);

            try {
                app.load(tpl);
                var doc2 = app.activeDocument;
                alert("Step 5b: app.load() SUCCESS\nDoc: " + doc2.name);
                doc2.close(SaveOptions.DONOTSAVECHANGES);
            } catch(e2) {
                alert("Step 5b FAILED: app.load() error:\n" + e2.message);
            }
        }
    }
} else {
    alert("No jobs found in: " + JOBS_DIR.fsName);
}

alert("Debug complete.");

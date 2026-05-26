// minimal_test.jsx — test if Photoshop can open a file at all
#target photoshop

var f = new File("C:/Varsany/template/adulttshirt.psd");
$.writeln("File exists: " + f.exists);
$.writeln("File path: " + f.fsName);

try {
    var doc = app.open(f);
    $.writeln("Opened OK: " + doc.name);
    doc.close(SaveOptions.DONOTSAVECHANGES);
    $.writeln("Done.");
} catch(e) {
    $.writeln("ERROR: " + e.message);
}

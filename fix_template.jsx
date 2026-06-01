// fix_template.jsx — clears CustomerImage_front layer content
#target photoshop

var templatePath = "C:\\Users\\yedhu\\AppData\\Roaming\\Adobe\\UXP\\PluginsStorage\\PHSP\\27\\Developer\\com.varsany.automation.worker\\PluginData\\templates\\adulttshirt.psd";

var f = new File(templatePath);
if (!f.exists) { alert("Template not found: " + templatePath); }
else {
    var doc = app.open(f);
    
    // Find and clear CustomerImage_front layer
    function findLayer(layers, name) {
        for (var i = 0; i < layers.length; i++) {
            if (layers[i].name === name) return layers[i];
        }
        return null;
    }
    
    var imgLayer = findLayer(doc.layers, "CustomerImage_front");
    if (imgLayer) {
        doc.activeLayer = imgLayer;
        // Select all and delete — makes layer transparent
        doc.selection.selectAll();
        doc.selection.clear();
        doc.selection.deselect();
        alert("CustomerImage_front cleared successfully!");
    } else {
        alert("Layer CustomerImage_front not found!");
    }
    
    // Save and close
    var opts = new PhotoshopSaveOptions();
    opts.layers = true;
    opts.embedColorProfile = true;
    doc.saveAs(f, opts, true);
    doc.close(SaveOptions.DONOTSAVECHANGES);
    alert("Template saved.");
}

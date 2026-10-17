"""
Pre-built ExtendScript templates for Adobe After Effects automation.
"""


def get_lower_third_snippet(title: str, subtitle: str, color_hex: str = "#00d2ff") -> str:
    """Returns an ExtendScript snippet that constructs an animated lower-third overlay."""
    safe_title = title.replace("'", "\\'")
    safe_sub = subtitle.replace("'", "\\'")

    return f"""
var comp = app.project.activeItem;
if (!comp || !(comp instanceof CompItem)) {{
    comp = app.project.items.addComp("LowerThirdComp", 1920, 1080, 1, 6, 30);
}}

// Add background solid box
var box = comp.layers.addSolid([0.05, 0.05, 0.08], "BoxBG", 600, 140, 1);
box.property("Position").setValue([450, 920, 0]);
box.property("Opacity").setValue(90);

// Animate Box In from left
var boxPos = box.property("Position");
boxPos.setValueAtTime(0, [-200, 920, 0]);
boxPos.setValueAtTime(0.6, [450, 920, 0]);

// Title text
var titleLayer = comp.layers.addText('{safe_title}');
var titleDoc = titleLayer.property("Source Text").value;
titleDoc.fontSize = 42;
titleDoc.fillColor = [1, 1, 1];
titleLayer.property("Source Text").setValue(titleDoc);
titleLayer.property("Position").setValue([200, 905, 0]);

// Subtitle text
var subLayer = comp.layers.addText('{safe_sub}');
var subDoc = subLayer.property("Source Text").value;
subDoc.fontSize = 24;
subDoc.fillColor = [0.2, 0.7, 1.0];
subLayer.property("Source Text").setValue(subDoc);
subLayer.property("Position").setValue([200, 945, 0]);

// Fade text in
titleLayer.property("Opacity").setValueAtTime(0.4, 0);
titleLayer.property("Opacity").setValueAtTime(0.8, 100);
subLayer.property("Opacity").setValueAtTime(0.6, 0);
subLayer.property("Opacity").setValueAtTime(1.0, 100);
"""

var FullFill = function (textObject, width, height) {
    textObject.setFixedSize(width, height);
    var padding = textObject.padding;
    width -= (padding.left + padding.right);
    height -= (padding.top + padding.bottom);

    var style = textObject.style;
    style.wrapWidth = Math.max(width, 0);
    var lineHeight = style.metrics.fontSize + style.strokeThickness;
    var lineSpacing = style.lineSpacing;
    var maxLines = Math.floor((height - lineSpacing) / (lineHeight + lineSpacing));
    style.maxLines = Math.max(maxLines, 0);
    textObject.updateText();
}
export default FullFill;
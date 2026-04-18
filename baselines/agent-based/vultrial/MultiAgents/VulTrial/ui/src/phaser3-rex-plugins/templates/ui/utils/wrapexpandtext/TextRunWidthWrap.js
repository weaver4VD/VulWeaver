import IsTextGameObject from '../../../../plugins/utils/text/IsTextGameObject.js';

var TextRunWidthWrap = function (textObject) {
    var RunWidthWrap = function (width) {
        var padding = textObject.padding;
        var wrapWidth = width - padding.left - padding.right;
        var style = textObject.style;
        if (IsTextGameObject(textObject)) {
            style.wordWrapWidth = wrapWidth;
            style.maxLines = 0;
        } else {
            if (style.wrapMode === 0) {
                style.wrapMode = 1;
            }
            style.wrapWidth = wrapWidth;
            style.maxLines = 0;
        }
        style.fixedWidth = width;
        style.fixedHeight = 0;
        textObject.updateText();

        textObject.minHeight = textObject.height;
        return textObject;
    }
    return RunWidthWrap;
}

export default TextRunWidthWrap;
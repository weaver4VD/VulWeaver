import { TextType, TagTextType, BitmapTextType } from '../../../../plugins/utils/text/GetTextObjectType.js'

var ResizeText = function (textObject, width, height) {
    height += (this.textLineHeight + this.textLineSpacing);
    if ((this.textObjectWidth === width) && (this._textObjectRealHeight === height)) {
        return;
    }
    this.textObjectWidth = width;
    this._textObjectRealHeight = height;

    switch (this.textObjectType) {
        case TextType:
        case TagTextType:
            textObject.setFixedSize(width, height);

            var style = textObject.style;
            var wrapWidth = Math.max(width, 0);
            if (this.textObjectType === TextType) {
                style.wordWrapWidth = wrapWidth;
            } else {
                if (style.wrapMode === 0) {
                    style.wrapMode = 1;
                }
                style.wrapWidth = wrapWidth;
            }
            break;
        case BitmapTextType:
            textObject.setMaxWidth(width);
            break;
    }
    this.setText();
}

export default ResizeText;
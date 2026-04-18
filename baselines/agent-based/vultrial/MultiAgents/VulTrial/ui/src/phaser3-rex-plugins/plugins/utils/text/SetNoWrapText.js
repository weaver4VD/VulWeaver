import {
    TextType, TagTextType, BitmapTextType
} from './GetTextObjectType.js';
import GetTextObjectType from './GetTextObjectType.js';

var SetNoWrapText = function (textObject, text) {
    var textObjectType = GetTextObjectType(textObject);
    switch (textObjectType) {
        case TextType:
            var style = textObject.style;
            var wordWrapWidth = style.wordWrapWidth;
            var wordWrapCallback = style.wordWrapCallback;
            style.wordWrapWidth = 0;
            style.wordWrapCallback = undefined;
            textObject.setText(text);
            style.wordWrapWidth = wordWrapWidth;
            style.wordWrapCallback = wordWrapCallback;
            break;

        case TagTextType:
            var style = textObject.style;
            var wrapMode = style.wrapMode;
            style.wrapMode = 0;
            textObject.setText(text);
            style.wrapMode = wrapMode;
            break;

        case BitmapTextType:
            var maxWidth = textObject._maxWidth;
            textObject._maxWidth = 0;
            textObject.setText(text);
            textObject._maxWidth = maxWidth;
            break;
    }
}

export default SetNoWrapText;
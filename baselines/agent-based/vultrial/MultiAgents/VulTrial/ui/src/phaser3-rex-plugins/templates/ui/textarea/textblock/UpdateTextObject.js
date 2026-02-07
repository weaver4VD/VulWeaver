import TextHeightToLinesCount from './TextHeightToLinesCount.js';
import LinesCountToTextHeight from './LinesCountToTextHeight.js';
import GetLines from './GetLines.js';
import SetNoWrapText from '../../../../plugins/utils/text/SetNoWrapText.js';
import ResetTextObjectPosition from './ResetTextObjectPosition.js';

var UpdateTextObject = function () {
    var startLineIndex = Math.max(Math.floor(TextHeightToLinesCount.call(this, -this.textOY)), 0);
    var textOffset = LinesCountToTextHeight.call(this, startLineIndex) + this.textOY;
    var text = GetLines.call(this, startLineIndex);
    SetNoWrapText(this.textObject, text);

    this.textObject.rexSizer.offsetY = textOffset;
    ResetTextObjectPosition.call(this);
    return this;
}
export default UpdateTextObject;
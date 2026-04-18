import TextToLines from "../../../../plugins/utils/text/TextToLines.js";

var SetText = function (text) {
    if (text !== undefined) {
        this.text = text;
    }
    this.lines = TextToLines(this.textObject, this.text, this.lines);
    this.linesCount = this.lines.length;
    this._textHeight = undefined;
    this._textVisibleHeight = undefined;

    this.updateTextObject();
    return this;
}
export default SetText;
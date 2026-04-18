import PreLayoutBase from '../../basesizer/PreLayout.js';

var PreLayout = function () {
    this._textLineHeight = undefined;
    this._textLineSpacing = undefined;
    this._visibleLinesCount = undefined;
    this._textHeight = undefined;
    this._textVisibleHeight = undefined;

    PreLayoutBase.call(this);
    return this;
}
export default PreLayout;
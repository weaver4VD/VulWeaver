import AppendText from './AppendText.js';

var SetText = function (text, style) {
    if (text === undefined) {
        text = '';
    }

    this.removeChildren();
    AppendText.call(this, text, style);

    this.dirty = true;
    return this;
};

export default SetText;
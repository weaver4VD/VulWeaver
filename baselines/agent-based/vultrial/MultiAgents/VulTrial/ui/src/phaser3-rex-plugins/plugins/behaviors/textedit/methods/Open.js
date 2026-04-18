import { SetLastOpenedEditor } from './LastOpenedEditor.js';
import IsFunction from '../../../utils/object/IsFunction.js';
import CreateInputTextFromText from './CreateInputText.js';
import NextTick from '../../../utils/time/NextTick.js';

const GetValue = Phaser.Utils.Objects.GetValue;
const Merge = Phaser.Utils.Objects.Merge;

var Open = function (config, onCloseCallback) {
    if (config === undefined) {
        config = {};
    }
    config = Merge(config, this.openConfig)

    SetLastOpenedEditor(this);

    if (IsFunction(config)) {
        onCloseCallback = config;
        config = undefined;
    }
    if (onCloseCallback === undefined) {
        onCloseCallback = GetValue(config, 'onClose', undefined);
    }

    var onOpenCallback = GetValue(config, 'onOpen', undefined);
    var customOnTextChanged = GetValue(config, 'onTextChanged', undefined);

    this.inputText = CreateInputTextFromText(this.parent, config)
        .on('textchange', function (inputText) {
            var text = inputText.text;
            if (customOnTextChanged) {
                customOnTextChanged(this.parent, text);
            } else {
                this.parent.text = text;
            }
        }, this)
        .setFocus();
    this.parent.setVisible(false);
    this.onClose = onCloseCallback;
    if (GetValue(config, 'enterClose', true)) {
        this.scene.input.keyboard.once('keydown-ENTER', this.close, this);
    }
    this.delayCall = NextTick(this.scene, function () {
        this.scene.input.once('pointerdown', this.close, this);
        if (onOpenCallback) {
            onOpenCallback(this.parent);
        }
        this.emit('open', this.parent);

    }, this);

    return this;
}

export default Open;
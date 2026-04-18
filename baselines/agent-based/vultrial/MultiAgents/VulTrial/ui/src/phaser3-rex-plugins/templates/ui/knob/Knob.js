import OverlapSizer from '../overlapsizer/OverlapSizer.js';
import ProgressBase from '../../../plugins/utils/progressbase/ProgressBase.js';
import CircularProgress from '../circularprogress/CircularProgress.js';
import InstallTouchPadEvents from './input/OnTouchPad.js';
import InstallPanPadEvents from './input/OnPanPad.js';
import TextObjectMethods from './TextObjectMethods.js';

const GetValue = Phaser.Utils.Objects.GetValue;
const SnapTo = Phaser.Math.Snap.To;

class Knob extends ProgressBase(OverlapSizer) {
    constructor(scene, config) {
        if (config === undefined) {
            config = {};
        }
        super(scene, config);
        this.type = 'rexKnob';

        this.bootProgressBase(config);
        var background = GetValue(config, 'background', undefined);
        var textObject = GetValue(config, 'text', undefined);

        if (background) {
            this.addBackground(background);
        }
        if (textObject) {
            config.textColor = undefined;
            config.textStrokeColor = undefined;
            this.setTextFormatCallback(
                GetValue(config, 'textFormatCallback', undefined),
                GetValue(config, 'textFormatCallbackScope', undefined)
            );
        }
        var knob = new CircularProgress(scene, config);
        knob.setDepth(GetValue(config, 'knobDepth', 0));
        knob._value = -1;
        scene.add.existing(knob);

        this.add(knob, 'knob');
        if (textObject) {
            this.add(textObject, 'text', 'center', 0, false);
            scene.children.moveBelow(knob, textObject);
        }

        this.addChildrenMap('background', background);
        this.addChildrenMap('knob', knob);
        this.addChildrenMap('text', textObject);

        this.setEnable(GetValue(config, 'enable', undefined));

        this.setGap(GetValue(config, 'gap', undefined));
        this.setValue(GetValue(config, 'value', 0), GetValue(config, 'min', undefined), GetValue(config, 'max', undefined));
        var inputMode = GetValue(config, 'input', 0);
        if (typeof (inputMode) === 'string') {
            inputMode = INPUTMODE[inputMode];
        }
        switch (inputMode) {
            case 0:
                InstallPanPadEvents.call(this);
                break;
            case 1:
                InstallTouchPadEvents.call(this);
                break;
        }
    }

    setEnable(enable) {
        if (enable === undefined) {
            enable = true;
        }
        this.enable = enable;
        return this;
    }

    setGap(gap) {
        this.gap = gap;
        return this;
    }
    get value() {
        return this.sizerChildren.knob.value;
    }
    set value(value) {
        if (this.gap !== undefined) {
            value = SnapTo(value, this.gap);
        }
        var oldValue = this.value;
        this.sizerChildren.knob.value = value;

        var newValue = this.value;
        if (oldValue !== newValue) {
            this.updateText();
            this.eventEmitter.emit('valuechange', newValue, oldValue, this.eventEmitter);
        }
    }

}

const INPUTMODE = {
    pan: 0,
    drag: 0,
    click: 1,
    none: -1,
}

Object.assign(
    Knob.prototype,
    TextObjectMethods,
);

export default Knob;
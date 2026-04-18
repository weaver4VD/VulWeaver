import Sizer from '../sizer/Sizer.js';
import AddChildMethods from './AddChildMethods.js';
import RemoveChildMethods from './RemoveChildMethods.js';
import ButtonGroup from '../utils/buttongroup/ButtonGroup.js';
import ButtonMethods from '../utils/buttongroup/ButtonMethods.js';
import ButtonStateMethods from '../utils/buttongroup/ButtonStateMethods.js';

const GetValue = Phaser.Utils.Objects.GetValue;

class Buttons extends Sizer {
    constructor(scene, config) {
        if (config === undefined) {
            config = {};
        }

        var buttonSpace = config.space;
        if (typeof (buttonSpace) === 'number') {
            config.space = { item: buttonSpace };
        }
        super(scene, config);
        this.type = 'rexButtons';
        this.buttonGroup = new ButtonGroup({
            parent: this,
            eventEmitter: GetValue(config, 'eventEmitter', this),
            groupName: GetValue(config, 'groupName', undefined),
            clickConfig: GetValue(config, 'click', undefined)
        })
            .setButtonsType(config)
        var background = GetValue(config, 'background', undefined);
        var buttons = GetValue(config, 'buttons', undefined);
        this.buttonsExpand = GetValue(config, 'expand', false);
        this.buttonsAlign = GetValue(config, 'align', undefined);

        if (background) {
            this.addBackground(background);
        }

        if (buttons) {
            this.addButtons(buttons);
        }

        this.addChildrenMap('background', background);
        this.addChildrenMap('buttons', this.buttonGroup.buttons);
    }

    destroy(fromScene) {
        if (!this.scene || this.ignoreDestroy) {
            return;
        }

        super.destroy(fromScene);
        this.buttonGroup.destroy();
        this.buttonGroup = undefined;
    }

    get buttons() {
        return this.buttonGroup.buttons;
    }

    get groupName() {
        return this.buttonGroup.groupName;
    }

    set groupName(value) {
        this.buttonGroup.groupName = value;
    }

    get eventEmitter() {
        return this.buttonGroup.eventEmitter;
    }
}

Object.assign(
    Buttons.prototype,
    AddChildMethods,
    RemoveChildMethods,
    ButtonMethods,
    ButtonStateMethods
);

export default Buttons;
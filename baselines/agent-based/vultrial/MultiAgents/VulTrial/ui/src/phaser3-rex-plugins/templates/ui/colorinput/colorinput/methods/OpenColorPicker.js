import CreateColorPicker from './CreateColorPicker.js';
import DropDown from '../../../dropdown/DropDown.js';

var OpenColorPicker = function () {
    if (this.colorPicker) {
        return;
    }
    var colorPicker = CreateColorPicker.call(this).layout();

    var dropDownBehavior = new DropDown(colorPicker, {
        duration: {
            in: this.colorPickerEaseInDuration,
            out: this.colorPickerEaseOutDuration
        },
        transitIn: this.colorPickerTransitInCallback,
        transitOut: this.colorPickerTransitOutCallback,
        expandDirection: this.colorPickerExpandDirection,

        alignTargetX: this,
        alignTargetY: this,

        bounds: this.colorPickerBounds,
        touchOutsideClose: true,
    })
        .on('open', function () {
            colorPicker.on('valuechange', function (value) {
                this.setValue(value);
            }, this);
        }, this)

        .on('close', function () {
            this.colorPicker = undefined;
            this.dropDownBehavior = undefined;
        }, this)

    this.colorPicker = colorPicker;
    this.dropDownBehavior = dropDownBehavior;

    this.pin(colorPicker);

    return this;
}

export default OpenColorPicker;
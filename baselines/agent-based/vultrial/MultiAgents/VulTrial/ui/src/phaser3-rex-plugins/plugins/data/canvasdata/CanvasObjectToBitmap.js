import CanvasData from './canvasdata/CanvasData.js';
import CanvasToData from './canvasdata/CanvasToData.js';
import BooleanBuffer from '../../utils/arraybuffers/BooleanBuffer.js';
import FillAlpha from './fillcallbacks/alpha.js';

const GetValue = Phaser.Utils.Objects.GetValue;

var CanvasObjectToBitmap = function (canvasObject, config, out) {
    if (config instanceof CanvasData) {
        out = config;
        config = undefined;
    }

    var x = GetValue(config, 'x', undefined);
    var y = GetValue(config, 'y', undefined);
    var width = GetValue(config, 'width', undefined);
    var height = GetValue(config, 'height', undefined);

    return CanvasToData(
        canvasObject.canvas,
        x, y, width, height,
        BooleanBuffer, FillAlpha, undefined,
        out);
};

export default CanvasObjectToBitmap;
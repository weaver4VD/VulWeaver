import AppendCommand from '../../../dynamictext/methods/AppendCommand.js';

var OnParseScrollCameraTag = function (textPlayer, parser, config) {
    var tagName = 'camera.scroll';
    parser
        .on(`+${tagName}`, function (x, y) {
            AppendCommand.call(textPlayer,
                tagName,
                Scroll,
                [x, y],
                textPlayer,
            );
            parser.skipEvent();
        })
        .on(`+${tagName}.to`, function (x, y, duration, ease) {
            AppendCommand.call(textPlayer,
                'camera.scroll.to',
                ScrollTo,
                [x, y, duration, ease],
                textPlayer,
            );
            parser.skipEvent();
        })
}

var Scroll = function (params) {
    this.targetCamera.setScroll(...params);
}

var ScrollTo = function (params) {
    var x = params[0];
    var y = params[1];
    var duration = params[2];
    var ease = params[3];
    var camera = this.targetCamera;
    var xSave = camera.scrollX;
    var ySave = camera.scrollY;
    camera.setScroll(x, y);
    x += camera.centerX;
    y += camera.centerY;
    camera.setScroll(xSave, ySave);
    camera.pan(x, y, duration, ease);
}

export default OnParseScrollCameraTag;
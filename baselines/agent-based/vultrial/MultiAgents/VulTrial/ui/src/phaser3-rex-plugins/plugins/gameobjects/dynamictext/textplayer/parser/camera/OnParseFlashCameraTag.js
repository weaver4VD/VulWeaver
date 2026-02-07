import AppendCommandBase from '../../../dynamictext/methods/AppendCommand.js';

var OnParseFlashCameraTag = function (textPlayer, parser, config) {
    var tagName = 'camera.flash';
    parser
        .on(`+${tagName}`, function (duration, red, green, blue) {
            AppendCommandBase.call(textPlayer,
                tagName,
                PlayFlashEffect,
                [duration, red, green, blue],
                textPlayer,
            );
            parser.skipEvent();
        })
}

var PlayFlashEffect = function (params) {
    this.targetCamera.flash(...params);
}

export default OnParseFlashCameraTag;
import AppendCommandBase from '../../../dynamictext/methods/AppendCommand.js';

var OnParseFadeInCameraTag = function (textPlayer, parser, config) {
    var tagName = 'camera.fadein';
    parser
        .on(`+${tagName}`, function (duration, red, green, blue) {
            AppendCommandBase.call(textPlayer,
                tagName,
                PlayFadeInEffect,
                [duration, red, green, blue],
                textPlayer,
            );
            parser.skipEvent();
        })
}

var PlayFadeInEffect = function (params) {
    this.targetCamera.fadeIn(...params);
}

export default OnParseFadeInCameraTag;
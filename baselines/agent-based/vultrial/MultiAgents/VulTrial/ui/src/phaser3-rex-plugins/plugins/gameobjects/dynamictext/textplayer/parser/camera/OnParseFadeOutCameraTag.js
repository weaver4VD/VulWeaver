import AppendCommandBase from '../../../dynamictext/methods/AppendCommand.js';

var OnParseFadeOutCameraTag = function (textPlayer, parser, config) {
    var tagName = 'camera.fadeout';
    parser
        .on(`+${tagName}`, function (duration, red, green, blue) {
            AppendCommandBase.call(textPlayer,
                tagName,
                PlayFadeOutEffect,
                [duration, red, green, blue],
                textPlayer,
            );
            parser.skipEvent();
        })
}

var PlayFadeOutEffect = function (params) {
    this.targetCamera.fadeOut(...params);
}

export default OnParseFadeOutCameraTag;
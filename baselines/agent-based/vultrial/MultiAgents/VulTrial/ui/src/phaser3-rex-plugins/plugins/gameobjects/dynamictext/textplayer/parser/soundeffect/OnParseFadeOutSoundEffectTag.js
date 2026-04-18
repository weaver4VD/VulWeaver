import AppendCommandBase from '../../../dynamictext/methods/AppendCommand.js';

var OnParseFadeOutSoundEffectTag = function (textPlayer, parser, config) {
    var tagName = 'se.fadeout';
    parser
        .on(`+${tagName}`, function (time, isStopped) {
            isStopped = (isStopped === 'stop');
            AppendCommandBase.call(textPlayer,
                tagName,
                FadeOutSoundEffect,
                [time, isStopped],
                textPlayer,
            );
            parser.skipEvent();
        })
        .on(`-${tagName}`, function () {
            parser.skipEvent();
        })


    var tagName = 'se2.fadeout';
    parser
        .on(`+${tagName}`, function (time, isStopped) {
            isStopped = (isStopped === 'stop');
            AppendCommandBase.call(textPlayer,
                tagName,
                FadeOutSoundEffect2,
                [time, isStopped],
                textPlayer,
            );
            parser.skipEvent();
        })
        .on(`-${tagName}`, function () {
            parser.skipEvent();
        })
}

var FadeOutSoundEffect = function (params) {
    this.soundManager.fadeOutSoundEffect(...params);
}

var FadeOutSoundEffect2 = function (params) {
    this.soundManager.fadeOutSoundEffect2(...params);
}
export default OnParseFadeOutSoundEffectTag;
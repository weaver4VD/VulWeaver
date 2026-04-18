import AppendCommandBase from '../../../dynamictext/methods/AppendCommand.js';

var OnParseFadeInSoundEffectTag = function (textPlayer, parser, config) {
    var tagName = 'se.fadein'
    parser
        .on(`+${tagName}`, function (time) {
            AppendCommandBase.call(textPlayer,
                tagName,
                FadeInSoundEffect,
                time,
                textPlayer,
            );
            parser.skipEvent();
        })
        .on(`-${tagName}`, function () {
            parser.skipEvent();
        })


    var tagName = 'se2.fadein'
    parser
        .on(`+${tagName}`, function (time) {
            AppendCommandBase.call(textPlayer,
                tagName,
                FadeInSoundEffect2,
                time,
                textPlayer,
            );
            parser.skipEvent();
        })
        .on(`-${tagName}`, function () {
            parser.skipEvent();
        })
}

var FadeInSoundEffect = function (time) {
    this.soundManager.fadeInSoundEffect(time);
}

var FadeInSoundEffect2 = function (time) {
    this.soundManager.fadeInSoundEffect2(time);
}

export default OnParseFadeInSoundEffectTag;
import AppendCommandBase from '../../../dynamictext/methods/AppendCommand.js';

var OnParseSetSoundEffectVolumeTag = function (textPlayer, parser, config) {
    var tagName = 'se.volume';
    parser
        .on(`+${tagName}`, function (volume) {
            AppendCommandBase.call(textPlayer,
                tagName,
                SetSoundEffectVolume,
                volume,
                textPlayer,
            );
            parser.skipEvent();
        })
        .on(`-${tagName}`, function () {
            parser.skipEvent();
        })


    var tagName = 'se2.volume';
    parser
        .on(`+${tagName}`, function (volume) {
            AppendCommandBase.call(textPlayer,
                tagName,
                SetSoundEffectVolume2,
                volume,
                textPlayer,
            );
            parser.skipEvent();
        })
        .on(`-${tagName}`, function () {
            parser.skipEvent();
        })
}

var SetSoundEffectVolume = function (volume) {
    this.soundManager.setSoundEffectVolume(volume, true);
}

var SetSoundEffectVolume2 = function (volume) {
    this.soundManager.setSoundEffectVolume2(volume, true);
}
export default OnParseSetSoundEffectVolumeTag;
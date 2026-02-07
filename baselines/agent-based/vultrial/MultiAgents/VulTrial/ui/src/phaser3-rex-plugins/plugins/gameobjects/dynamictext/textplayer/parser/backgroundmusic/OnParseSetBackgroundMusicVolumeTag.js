import AppendCommandBase from '../../../dynamictext/methods/AppendCommand.js';

var OnParseSetBackgroundMusicVolumeTag = function (textPlayer, parser, config) {
    var tagName = 'bgm.volume';
    parser
        .on(`+${tagName}`, function (volume) {
            AppendCommandBase.call(textPlayer,
                tagName,
                SetBackgroundMusicVolume,
                volume,
                textPlayer,
            );
            parser.skipEvent();
        })
        .on(`-${tagName}`, function () {
            parser.skipEvent();
        })


    var tagName = 'bgm2.volume';
    parser
        .on(`+${tagName}`, function (volume) {
            AppendCommandBase.call(textPlayer,
                tagName,
                SetBackgroundMusicVolume2,
                volume,
                textPlayer,
            );
            parser.skipEvent();
        })
        .on(`-${tagName}`, function () {
            parser.skipEvent();
        })
}

var SetBackgroundMusicVolume = function (volume) {
    this.soundManager.setBackgroundMusicVolume(volume);
}

var SetBackgroundMusicVolume2 = function (volume) {
    this.soundManager.setBackgroundMusicVolume2(volume);
}
export default OnParseSetBackgroundMusicVolumeTag;
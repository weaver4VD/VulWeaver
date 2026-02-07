import AppendCommandBase from '../../../dynamictext/methods/AppendCommand.js';

var OnParsePlayBackgroundMusicTag = function (textPlayer, parser, config) {
    var tagName = 'bgm';
    parser
        .on(`+${tagName}`, function (name, fadeInTime) {
            AppendCommandBase.call(textPlayer,
                tagName,
                PlayBackgroundMusic,
                [name, fadeInTime],
                textPlayer,
            );
            parser.skipEvent();
        })
        .on(`-${tagName}`, function () {
            AppendCommandBase.call(textPlayer,
                'bgm.stop',
                StopBackgroundMusic,
                undefined,
                textPlayer,
            );
            parser.skipEvent();
        })


    var tagName = 'bgm2';
    parser
        .on(`+${tagName}`, function (name, fadeInTime) {
            AppendCommandBase.call(textPlayer,
                tagName,
                PlayBackgroundMusic2,
                [name, fadeInTime],
                textPlayer,
            );
            parser.skipEvent();
        })
        .on(`-${tagName}`, function () {
            AppendCommandBase.call(textPlayer,
                'bgm2.stop',
                StopBackgroundMusic2,
                undefined,
                textPlayer,
            );
            parser.skipEvent();
        })
}

var PlayBackgroundMusic = function (params) {
    var name = params[0];
    var fadeInTime = params[1];
    this.soundManager.playBackgroundMusic(name);
    if (fadeInTime) {
        this.soundManager.fadeInBackgroundMusic(fadeInTime);
    }
}

var StopBackgroundMusic = function () {
    this.soundManager.stopBackgroundMusic();
}

var PlayBackgroundMusic2 = function (params) {
    var name = params[0];
    var fadeInTime = params[1];
    this.soundManager.playBackgroundMusic2(name);
    if (fadeInTime) {
        this.soundManager.fadeInBackgroundMusic2(fadeInTime);
    }
}

var StopBackgroundMusic2 = function () {
    this.soundManager.stopBackgroundMusic2();
}

export default OnParsePlayBackgroundMusicTag;
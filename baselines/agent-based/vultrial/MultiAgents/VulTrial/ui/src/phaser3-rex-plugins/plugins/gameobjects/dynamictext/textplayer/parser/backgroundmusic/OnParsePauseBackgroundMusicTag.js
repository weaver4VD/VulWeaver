import AppendCommandBase from '../../../dynamictext/methods/AppendCommand.js';

var OnParsePauseBackgroundMusicTag = function (textPlayer, parser, config) {
    var tagName = 'bgm.pause';
    parser
        .on(`+${tagName}`, function () {
            AppendCommandBase.call(textPlayer,
                tagName,
                PauseBackgroundMusic,
                undefined,
                textPlayer,
            );
            parser.skipEvent();
        })
        .on(`-${tagName}`, function () {
            AppendCommandBase.call(textPlayer,
                'bgm.resume',
                ResumeBackgroundMusic,
                undefined,
                textPlayer,
            );
            parser.skipEvent();
        })


    var tagName = 'bgm2.pause';
    parser
        .on(`+${tagName}`, function () {
            AppendCommandBase.call(textPlayer,
                tagName,
                PauseBackgroundMusic2,
                undefined,
                textPlayer,
            );
            parser.skipEvent();
        })
        .on(`-${tagName}`, function () {
            AppendCommandBase.call(textPlayer,
                'bgm2.resume',
                ResumeBackgroundMusic2,
                undefined,
                textPlayer,
            );
            parser.skipEvent();
        })
}

var PauseBackgroundMusic = function () {
    this.soundManager.pauseBackgroundMusic();
}

var ResumeBackgroundMusic = function () {
    this.soundManager.resumeBackgroundMusic();
}

var PauseBackgroundMusic2 = function () {
    this.soundManager.pauseBackgroundMusic2();
}

var ResumeBackgroundMusic2 = function () {
    this.soundManager.resumeBackgroundMusic2();
}

export default OnParsePauseBackgroundMusicTag;
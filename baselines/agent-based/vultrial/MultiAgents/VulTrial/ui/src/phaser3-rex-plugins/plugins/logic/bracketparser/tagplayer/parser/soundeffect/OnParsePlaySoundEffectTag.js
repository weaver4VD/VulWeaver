var OnParsePlaySoundEffectTag = function (tagPlayer, parser, config) {
    var tagName = 'se';
    parser
        .on(`+${tagName}`, function (name, fadeInTime) {
            if (this.skipSoundEffect) {
                return;
            }

            tagPlayer.soundManager.playSoundEffect(name);
            if (fadeInTime) {
                tagPlayer.soundManager.fadeInSoundEffect(fadeInTime);
            }

            parser.skipEvent();
        })
        .on(`-${tagName}`, function () {
            parser.skipEvent();
        })


    var tagName = 'se2';
    parser
        .on(`+${tagName}`, function (name, fadeInTime) {
            if (this.skipSoundEffect) {
                return;
            }

            tagPlayer.soundManager.playSoundEffect2(name);
            if (fadeInTime) {
                tagPlayer.soundManager.fadeInSoundEffect2(fadeInTime);
            }

            parser.skipEvent();
        })
        .on(`-${tagName}`, function () {
            parser.skipEvent();
        })
}

export default OnParsePlaySoundEffectTag;
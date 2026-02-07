import AppendCommandBase from '../../../dynamictext/methods/AppendCommand.js';

var IsPauseAnimationTag = function (tags, goType) {
    return (tags.length === 3) && (tags[0] === goType) && (tags[2] === 'pause');
}

var OnParsePauseAnimationTag = function (textPlayer, parser, config) {
    var goType = config.name;
    parser
        .on('+', function (tag) {
            if (parser.skipEventFlag) {
                return;
            }
            var tags = tag.split('.');
            var name;
            if (IsPauseAnimationTag(tags, goType)) {
                name = tags[1];
            } else {
                return;
            }

            AppendCommandBase.call(textPlayer,
                `${goType}.pause`,
                PauseAnimation,
                [goType, name],
                textPlayer,
            );

            parser.skipEvent();
        })
}

var PauseAnimation = function (params) {
    var goType, args;
    [goType, ...args] = params;
    var gameObjectManager = this.getGameObjectManager(goType);
    gameObjectManager.pauseAnimation(...args);
}

export default OnParsePauseAnimationTag;
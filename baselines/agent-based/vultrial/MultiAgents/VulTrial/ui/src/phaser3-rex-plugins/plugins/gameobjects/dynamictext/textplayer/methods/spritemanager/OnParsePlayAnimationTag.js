import AppendCommandBase from '../../../dynamictext/methods/AppendCommand.js';

var IsPlayAnimationTag = function (tags, goType) {
    return (tags.length === 3) && (tags[0] === goType) && (tags[2] === 'play');
}

var IsStopAnimationTag = function (tags, goType) {
    return (tags.length === 3) && (tags[0] === goType) && (tags[2] === 'stop');
}

var OnParsePlayAnimationTag = function (textPlayer, parser, config) {
    var goType = config.name;
    parser
        .on('+', function (tag, ...keys) {
            if (parser.skipEventFlag) {
                return;
            }
            var tags = tag.split('.');
            var name;
            if (IsPlayAnimationTag(tags, goType)) {
                name = tags[1];
            } else {
                return;
            }

            AppendCommandBase.call(textPlayer,
                `${goType}.play`,
                PlayAnimation,
                [goType, name, keys],
                textPlayer,
            );

            parser.skipEvent();
        })
        .on('+', function (tag) {
            if (parser.skipEventFlag) {
                return;
            }
            var tags = tag.split('.');
            var name;
            if (IsStopAnimationTag(tags, goType)) {
                name = tags[1];
            } else {
                return;
            }

            AppendCommandBase.call(textPlayer,
                `${goType}.stop`,
                StopAnimation,
                [goType, name],
                textPlayer,
            );

            parser.skipEvent();
        })
        .on('-', function (tag) {
            if (parser.skipEventFlag) {
                return;
            }
            var tags = tag.split('.');
            var name;
            if (IsPlayAnimationTag(tags, goType)) {
                name = tags[1];
            } else {
                return;
            }

            AppendCommandBase.call(textPlayer,
                `${goType}.stop`,
                StopAnimation,
                [goType, name],
                textPlayer,
            );

            parser.skipEvent();
        })
}

var PlayAnimation = function (params) {
    var goType, name, keys;
    [goType, name, keys] = params;
    var key = keys.shift();
    var gameObjectManager = this.getGameObjectManager(goType);
    gameObjectManager.playAnimation(name, key);
    if (keys.length > 0) {
        gameObjectManager.chainAnimation(name, keys);
    }
}

var StopAnimation = function (params) {
    var goType, args;
    [goType, ...args] = params;
    var gameObjectManager = this.getGameObjectManager(goType);
    gameObjectManager.stopAnimation(...args);
}

export default OnParsePlayAnimationTag;
import AppendCommandBase from '../../../dynamictext/methods/AppendCommand.js';

var IsAddGameObjectTag = function (tags, goType) {
    return (tags.length === 2) && (tags[0] === goType)
}

var OnParseAddGameObjectTag = function (textPlayer, parser, config) {
    var goType = config.name;
    parser
        .on('+', function (tag, ...args) {
            if (parser.skipEventFlag) {
                return;
            }
            var tags = tag.split('.');
            var name;
            if (IsAddGameObjectTag(tags, goType)) {
                name = tags[1];
            } else {
                return;
            }

            AppendCommandBase.call(textPlayer,
                `${goType}.add`,
                AddGameObject,
                [goType, name, ...args],
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
            if (IsAddGameObjectTag(tags, goType)) {
                name = tags[1];
            } else {
                return;
            }

            AppendCommandBase.call(textPlayer,
                `${goType}.remove`,
                RemoveGameObject,
                [goType, name],
                textPlayer,
            );

            parser.skipEvent();
        })
}

var AddGameObject = function (params) {
    var goType, args;
    [goType, ...args] = params;
    var gameObjectManager = this.getGameObjectManager(goType);
    gameObjectManager.add(...args);
}

var RemoveGameObject = function (params) {
    var goType, args;
    [goType, ...args] = params;
    var gameObjectManager = this.getGameObjectManager(goType);
    gameObjectManager.remove(...args);
}

export default OnParseAddGameObjectTag;
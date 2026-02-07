import AppendCommandBase from '../../../dynamictext/methods/AppendCommand.js';

var OnParseRemoveAllGameObjectsTag = function (textPlayer, parser, config) {
    var goType = config.name;
    parser
        .on('-', function (tag) {
            if (parser.skipEventFlag) {
                return;
            }
            if (tag === goType) {
            } else {
                return;
            }

            AppendCommandBase.call(textPlayer,
                `${goType}.removeall`,
                RemoveAllSprites,
                goType,
                textPlayer,
            );
            parser.skipEvent();
        })
}

var RemoveAllSprites = function (goType) {
    var gameObjectManager = this.getGameObjectManager(goType);
    gameObjectManager.removeAll();
}

export default OnParseRemoveAllGameObjectsTag;
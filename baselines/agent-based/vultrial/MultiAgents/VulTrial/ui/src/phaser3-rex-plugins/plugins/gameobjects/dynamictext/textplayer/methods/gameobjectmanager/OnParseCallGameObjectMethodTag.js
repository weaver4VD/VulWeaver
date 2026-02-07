import AppendCommandBase from '../../../dynamictext/methods/AppendCommand.js';

var IsPropTag = function (tags, goType) {
    return (tags.length === 3) && (tags[0] === goType);
}

var OnParseCallGameObjectMethodTag = function (textPlayer, parser, config) {
    var goType = config.name;
    parser
        .on(`+`, function (tag, ...parameters) {
            if (parser.skipEventFlag) {
                return;
            }
            var tags = tag.split('.');
            var name, prop;
            if (IsPropTag(tags, goType)) {
                name = tags[1];
                prop = tags[2];
            } else {
                return;
            }

            AppendCommandBase.call(textPlayer,
                `${goType}.call`,
                CallMethod,
                [goType, name, prop, ...parameters],
                textPlayer,
            );

            parser.skipEvent();
        })
}

var CallMethod = function (params) {
    var goType, name, prop, args;
    [goType, name, prop, ...args] = params;

    var eventName = `${goType}.${prop}`;
    this.emit(
        eventName,
        name, ...args
    );
    if (this.listenerCount(eventName) > 0) {
        return;
    }

    var gameObjectManager = this.getGameObjectManager(goType);
    if (gameObjectManager.hasMethod(name, prop)) {
        gameObjectManager.call(name, prop, ...args);
    } else {
        gameObjectManager.setProperty(name, prop, args[0]);
    }

}

export default OnParseCallGameObjectMethodTag;
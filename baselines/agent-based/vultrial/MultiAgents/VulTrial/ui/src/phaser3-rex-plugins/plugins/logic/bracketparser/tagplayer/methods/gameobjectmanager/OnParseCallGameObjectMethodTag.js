var IsPropTag = function (tags, goType) {
    return (tags.length === 3) && (tags[0] === goType);
}

var OnParseCallGameObjectMethodTag = function (tagPlayer, parser, config) {
    var goType = config.name;
    var gameObjectManager = tagPlayer.getGameObjectManager(goType);
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

            var eventName = `${goType}.${prop}`;
            tagPlayer.emit(
                eventName,
                name, ...parameters
            );
            if (tagPlayer.listenerCount(eventName) > 0) {
                parser.skipEvent();
                return;
            }

            if (gameObjectManager.hasMethod(name, prop)) {
                gameObjectManager.call(name, prop, ...parameters);
            } else {
                gameObjectManager.setProperty(name, prop, parameters[0]);
            }

            parser.skipEvent();
        })
}

export default OnParseCallGameObjectMethodTag;
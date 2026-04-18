var OnParseRemoveAllGameObjectsTag = function (tagPlayer, parser, config) {
    var goType = config.name;
    var gameObjectManager = tagPlayer.getGameObjectManager(goType);
    parser
        .on('-', function (tag) {
            if (parser.skipEventFlag) {
                return;
            }
            if (tag === goType) {
            } else {
                return;
            }

            gameObjectManager.removeAll();
            parser.skipEvent();
        })
}

export default OnParseRemoveAllGameObjectsTag;
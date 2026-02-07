var OnParseSetTextTag = function (tagPlayer, parser, config) {
    var goType = config.name;
    var gameObjectManager = tagPlayer.getGameObjectManager(goType);
    tagPlayer.on(`${goType}.text`, function (name) {
        gameObjectManager.clearText(name);
        tagPlayer.setContentCallback(function (content) {
            gameObjectManager.appendText(name, content);
        });
    });
}

export default OnParseSetTextTag;
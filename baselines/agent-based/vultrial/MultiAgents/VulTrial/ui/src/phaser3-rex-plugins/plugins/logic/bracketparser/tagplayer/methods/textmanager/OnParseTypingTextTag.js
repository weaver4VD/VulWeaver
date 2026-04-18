var OnParseTypingTextTag = function (tagPlayer, parser, config) {
    var goType = config.name;
    var gameObjectManager = tagPlayer.getGameObjectManager(goType);
    tagPlayer.on(`${goType}.typing`, function (name, speed) {
        gameObjectManager.clearTyping(name);
        tagPlayer.setContentCallback(function (content) {
            if (speed !== undefined) {
                gameObjectManager.setTypingSpeed(name, speed);
            }
            gameObjectManager.typing(name, content);
        });
    });
}

export default OnParseTypingTextTag;
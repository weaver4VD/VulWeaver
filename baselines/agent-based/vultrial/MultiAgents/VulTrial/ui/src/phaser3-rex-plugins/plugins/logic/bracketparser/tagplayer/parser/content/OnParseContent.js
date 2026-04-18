var OnParseContent = function (tagPlayer, parser, config) {
    parser
        .on('content', function (content) {
            if (parser.skipEventFlag) {
                return;
            }

            if (content === '\n') {
                return;
            }

            content = content.replaceAll('\\n', '\n');

            var callback = tagPlayer.contentCallback;
            if (callback) {
                var scope = tagPlayer.contentCallbackScope;
                if (scope) {
                    callback.call(scope, content);
                } else {
                    callback(content);
                }
                parser.skipEvent();
            }

            tagPlayer.emit(`+${parser.lastTagStart}#content`, content);
            tagPlayer.emit('content', content);
        })
}

export default OnParseContent;
import AppendCommandBase from '../../../dynamictext/methods/AppendCommand.js';

var OnParseCustomTag = function (textPlayer, parser, config) {
    parser
        .on('start', function () {
            textPlayer.emit('parser.start', parser);
        })
        .on('+', function (tagName, ...value) {
            if (parser.skipEventFlag) {
                return;
            }

            var startTag = `+${tagName}`;
            var param = value;
            textPlayer.emit(`parser.${startTag}`, parser, ...value, param);
            AppendCommand(textPlayer, startTag, param);
        })
        .on('-', function (tagName) {
            if (parser.skipEventFlag) {
                return;
            }

            var endTag = `-${tagName}`;
            var param = [];
            textPlayer.emit(`parser.${endTag}`, parser, param);
            AppendCommand(textPlayer, endTag, param);
        })
        .on('complete', function () {
            textPlayer.emit('parser.complete', parser);
        })
}

var FireEvent = function (param, tagName) {
    var eventName = `tag.${tagName}`;
    if (param == null) {
        this.emit(eventName);
    } else {
        this.emit(eventName, ...param);
    }

}

var AppendCommand = function (textPlayer, name, param) {
    AppendCommandBase.call(textPlayer,
        name,
        FireEvent,
        param,
        textPlayer,
    );
}

export default OnParseCustomTag;
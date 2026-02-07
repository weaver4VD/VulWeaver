

var PreProcess = function (parser, source) {
    var comentLineStart = parser.commentLineStart;
    var lines = source.split('\n');
    for (var i = 0, cnt = lines.length; i < cnt; i++) {
        var line = lines[i];
        if (line === '') {

        } else if (line.trim().length === 0) {
            lines[i] = '';

        } else if (comentLineStart && line.startsWith(comentLineStart)) {
            lines[i] = '';
        }
    }

    return lines.join('');
}

export default PreProcess;
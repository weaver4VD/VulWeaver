var IsInvalidLine = function (line) {
    if (line.length === 0 || !line.trim()) {
        return true;
    }
    if (line.trimStart().substring(0, 2) === '//') {
        return true;
    }
}

export default IsInvalidLine;
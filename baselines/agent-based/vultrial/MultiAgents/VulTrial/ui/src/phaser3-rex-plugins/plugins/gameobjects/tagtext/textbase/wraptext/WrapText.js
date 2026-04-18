import CONST from '../../../textbase/const.js';

const NO_NEWLINE = CONST.NO_NEWLINE;
const RAW_NEWLINE = CONST.RAW_NEWLINE;
const WRAPPED_NEWLINE = CONST.WRAPPED_NEWLINE;
const NO_WRAP = CONST.NO_WRAP;
const WORD_WRAP = CONST.WORD_WRAP;
const CHAR_WRAP = CONST.CHAR_WRAP;
const splitRegExp = CONST.SPLITREGEXP;

var WrapText = function (text, getTextWidth, wrapMode, wrapWidth, offset, wrapTextLinesPool) {
    if (wrapWidth <= 0) {
        wrapMode = NO_WRAP;
    }

    var retLines = [];
    if (!text || !text.length) {
        return retLines;
    }

    var isNoWrap = (wrapMode === NO_WRAP);
    var isWordWrap = (wrapMode === WORD_WRAP);

    var lines = text.split(splitRegExp),
        line, remainWidth, newLineMode;
    for (var i = 0, linesLen = lines.length; i < linesLen; i++) {
        line = lines[i];
        newLineMode = (i === (linesLen - 1)) ? NO_NEWLINE : RAW_NEWLINE;

        if (isNoWrap) {
            var textWidth = getTextWidth(line);
            retLines.push(wrapTextLinesPool.getLine(line, textWidth, newLineMode));
            continue;
        }

        remainWidth = (i === 0) ? (wrapWidth - offset) : wrapWidth;
        if (line.length <= 100) {
            var textWidth = getTextWidth(line);
            if (textWidth <= remainWidth) {
                retLines.push(wrapTextLinesPool.getLine(line, textWidth, newLineMode));
                continue;
            }
        }

        var tokenArray, isSpaceCharacterEnd;
        if (isWordWrap) {
            tokenArray = line.split(' ');
            isSpaceCharacterEnd = (tokenArray[tokenArray.length - 1] === '');
            if (isSpaceCharacterEnd) {
                tokenArray.length -= 1;
            }
        } else {
            tokenArray = line;
        }
        var token, tokenWidth, isLastToken;
        var lineText = '', lineWidth = 0;
        var currLineWidth;
        var whiteSpaceWidth = (isWordWrap) ? getTextWidth(' ') : undefined;
        for (var j = 0, tokenLen = tokenArray.length; j < tokenLen; j++) {
            token = tokenArray[j];
            tokenWidth = getTextWidth(token);

            isLastToken = (j === (tokenLen - 1));
            if (isWordWrap && (!isLastToken || isSpaceCharacterEnd)) {
                token += ' ';
                tokenWidth += whiteSpaceWidth;
            }
            if (isWordWrap && (tokenWidth > wrapWidth)) {
                if (lineText !== '') {
                    retLines.push(wrapTextLinesPool.getLine(lineText, lineWidth, WRAPPED_NEWLINE));

                } else if ((j === 0) && (offset > 0)) {
                    retLines.push(wrapTextLinesPool.getLine('', 0, WRAPPED_NEWLINE));

                }
                retLines.push(...WrapText(token, getTextWidth, CHAR_WRAP, wrapWidth, 0, wrapTextLinesPool));
                var lastwordBreakLine = retLines.pop();
                lineText = lastwordBreakLine.text;
                lineWidth = lastwordBreakLine.width;
                wrapTextLinesPool.freeLine(lastwordBreakLine);
                if (lineText === ' ') {
                    lineText = '';
                    lineWidth = 0;
                }
                continue;
            }

            currLineWidth = lineWidth + tokenWidth;
            if (currLineWidth > remainWidth) {
                retLines.push(wrapTextLinesPool.getLine(lineText, lineWidth, WRAPPED_NEWLINE));
                lineText = token;
                lineWidth = tokenWidth;
                remainWidth = wrapWidth;

            } else {
                lineText += token;
                lineWidth = currLineWidth;
            }

            if (isLastToken) {
                retLines.push(wrapTextLinesPool.getLine(lineText, lineWidth, newLineMode));
            }
        }

    }

    return retLines;
};

export default WrapText;
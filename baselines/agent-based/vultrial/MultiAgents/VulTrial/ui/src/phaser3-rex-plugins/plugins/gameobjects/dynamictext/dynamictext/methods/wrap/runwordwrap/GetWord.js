import { CharTypeName } from '../../../bob/Types.js';

var GetWord = function (children, startIndex, charMode, result) {
    if (result === undefined) {
        result = { word: [], width: 0 };
    }

    result.word.length = 0;

    var endIndex = children.length;
    var currentIndex = startIndex;
    var word = result.word, wordWidth = 0;
    while (currentIndex < endIndex) {
        var child = children[currentIndex];
        if (!child.renderable) {
            word.push(child);
            currentIndex++;
            continue;
        }

        var text = (child.type === CharTypeName) ? child.text : null;
        if ((text !== null) &&
            (text !== ' ') && (text !== '\n') && (text !== '\f')
        ) {
            word.push(child);
            wordWidth += child.outerWidth;
            currentIndex++;
        } else {
            if (currentIndex === startIndex) {
                word.push(child);
                wordWidth += child.outerWidth;
            }
            break;
        }

        if (charMode) {
            break;
        }
    }

    result.width = wordWidth;
    return result;
}

export default GetWord;
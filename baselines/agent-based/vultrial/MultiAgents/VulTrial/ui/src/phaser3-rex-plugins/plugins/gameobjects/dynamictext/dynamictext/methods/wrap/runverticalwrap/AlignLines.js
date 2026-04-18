import GetChildrenAlign from '../GetChildrenAlign.js';
import OffsetChildren from '../OffsetChildren.js';

var AlignLines = function (result, width, height) {
    var hAlign = result.hAlign,
        vAlign = result.vAlign;

    var offsetX, offsetY;

    var rtl = result.rtl;
    var lines = result.lines,
        lineWidth = result.lineWidth,
        linesWidth = result.linesWidth;
    switch (hAlign) {
        case 1:
        case 'center':
            offsetX = (width - linesWidth) / 2
            break;

        case 2:
        case 'right':
            offsetX = width - linesWidth;
            break;

        default:
            offsetX = 0;
            break;
    }
    if (rtl) {
        offsetX += lineWidth;
    }

    for (var li = 0, lcnt = lines.length; li < lcnt; li++) {
        var line = lines[(rtl) ? (lcnt - li - 1) : li];
        var children = line.children;
        var lineHeight = line.height;

        var lineVAlign = GetChildrenAlign(children);
        if (lineVAlign === undefined) {
            lineVAlign = vAlign;
        }

        switch (lineVAlign) {
            case 1:
            case 'center':
                offsetY = (height - lineHeight) / 2;
                break;

            case 2:
            case 'bottom':
                offsetY = height - lineHeight;
                break;

            default:
                offsetY = 0;
                break;
        }

        OffsetChildren(children, offsetX, offsetY);

        offsetX += lineWidth;
    }
}

export default AlignLines;
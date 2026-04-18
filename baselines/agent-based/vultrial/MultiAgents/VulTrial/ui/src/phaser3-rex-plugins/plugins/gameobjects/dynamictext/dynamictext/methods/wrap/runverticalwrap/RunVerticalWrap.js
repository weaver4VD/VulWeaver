import { SetPadding } from '../../../../../../utils/padding/PaddingMethods.js';
import AlignLines from './AlignLines.js';
import { IsNewLineChar, IsPageBreakChar } from '../../../bob/Types.js';

const GetValue = Phaser.Utils.Objects.GetValue;

var RunVerticalWrap = function (config) {
    var startIndex = GetValue(config, 'start', 0);

    SetPadding(this.wrapPadding, GetValue(config, 'padding', 0));
    var paddingVertical = this.padding.top + this.padding.bottom + this.wrapPadding.top + this.wrapPadding.bottom;
    var paddingHorizontal = this.padding.left + this.padding.right + this.wrapPadding.left + this.wrapPadding.right;

    var lineWidth = GetValue(config, 'lineWidth', undefined);
    var maxLines;
    if (lineWidth === undefined) {
        maxLines = GetValue(config, 'maxLines', 0);
        if (this.fixedWidth > 0) {
            var innerWidth = this.fixedWidth - paddingHorizontal;
            lineWidth = innerWidth / maxLines;
        } else {
            lineWidth = 0;
        }
    } else {
        if (this.fixedWidth > 0) {
            maxLines = GetValue(config, 'maxLines', undefined);
            if (maxLines === undefined) {
                var innerWidth = this.fixedWidth - paddingHorizontal;
                maxLines = Math.floor(innerWidth / lineWidth) + 1;
            }
        } else {
            maxLines = GetValue(config, 'maxLines', 0);
        }

    }
    var showAllLines = (maxLines === 0);
    var fixedChildHeight = GetValue(config, 'fixedChildHeight', undefined);
    if (fixedChildHeight === undefined) {
        var charPerLine = GetValue(config, 'charPerLine', undefined);
        if (charPerLine !== undefined) {
            var innerHeight = this.fixedHeight - paddingVertical;
            fixedChildHeight = Math.floor(innerHeight / charPerLine);
        } else {
        }
    }
    var wrapHeight = GetValue(config, 'wrapHeight', undefined);
    if (wrapHeight === undefined) {
        if (this.fixedHeight > 0) {
            wrapHeight = this.fixedHeight - paddingVertical;
        } else {
            wrapHeight = Infinity;
        }
    }

    var letterSpacing = GetValue(config, 'letterSpacing', 0);

    var rtl = GetValue(config, 'rtl', true);
    var hAlign = GetValue(config, 'hAlign', rtl ? 2 : 0);
    var vAlign = GetValue(config, 'vAlign', 0);

    var result = {
        callback: 'runVerticalWrap',
        start: startIndex,
        isLastPage: false,
        padding: this.wrapPadding,
        lineWidth: lineWidth,
        maxLines: maxLines,
        fixedChildHeight: fixedChildHeight,
        wrapHeight: wrapHeight,
        letterSpacing: letterSpacing,
        hAlign: hAlign,
        vAlign: vAlign,
        rtl: rtl,
        children: [],
        lines: [],
        maxLineHeight: 0,
        linesWidth: 0
    }
    var children = this.children;
    for (var i = 0, cnt = children.length; i < cnt; i++) {
        children[i].setActive(false);
    }
    wrapHeight += letterSpacing;
    var startX = this.padding.left + this.wrapPadding.left,
        startY = this.padding.top + this.wrapPadding.top,
        x = startX,
        y = startY;
    var remainderHeight = wrapHeight,
        childIndex = startIndex,
        lastChildIndex = children.length;
    var resultChildren = result.children;
    var resultLines = result.lines,
        lastLine = [], lastLineHeight = 0, maxLineHeight = 0;
    while (childIndex < lastChildIndex) {
        var child = children[childIndex];
        childIndex++;
        if (!child.renderable) {
            child.setActive();
            resultChildren.push(child);
            lastLine.push(child);
            continue;
        }

        var childHeight = ((fixedChildHeight !== undefined) ? fixedChildHeight : child.height) + letterSpacing;
        var isNewLineChar = IsNewLineChar(child);
        var isPageBreakChar = IsPageBreakChar(child);
        var isControlChar = isNewLineChar || isPageBreakChar;
        if ((remainderHeight < childHeight) || isControlChar) {
            if (isNewLineChar) {
                child.setActive().setPosition(x, y).setOrigin(0.5);
                resultChildren.push(child);
                lastLine.push(child);
            }
            x = startX;
            y = startY;
            remainderHeight = wrapHeight;
            resultLines.push({ children: lastLine, height: lastLineHeight });
            maxLineHeight = Math.max(maxLineHeight, lastLineHeight);

            lastLineHeight = 0;
            lastLine = [];

            var isPageEnd = isPageBreakChar ||
                (!showAllLines && (resultLines.length === maxLines));
            if (isPageEnd) {
                break;
            } else if (isControlChar) {
                continue;
            }
        }
        remainderHeight -= childHeight;
        lastLineHeight += childHeight;

        child.setActive().setPosition(x, y).setOrigin(0.5);
        resultChildren.push(child);
        lastLine.push(child);
        y += childHeight;
    }

    if (lastLine.length > 0) {
        resultLines.push({ children: lastLine, height: lastLineHeight });
        maxLineHeight = Math.max(maxLineHeight, lastLineHeight);
    }

    result.start += resultChildren.length;
    result.isLastPage = (result.start === lastChildIndex);
    result.maxLineHeight = maxLineHeight;
    result.linesWidth = (resultLines.length * lineWidth);
    var width = (this.fixedWidth > 0) ? this.fixedWidth : (result.linesWidth + paddingHorizontal);
    var height = (this.fixedHeight > 0) ? this.fixedHeight : (result.maxLineHeight + paddingVertical);
    var innerWidth = width - paddingHorizontal;
    var innerHeight = height - paddingVertical;
    AlignLines(result, innerWidth, innerHeight);
    this.setCanvasSize(width, height);
    for (var i = 0, cnt = resultChildren.length; i < cnt; i++) {
        var child = resultChildren[i];
        if (!child.renderable) {
            continue;
        }
        child.x0 = child.x;
        child.y0 = child.y;
    }

    return result;
}

export default RunVerticalWrap;
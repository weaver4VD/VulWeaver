var SetInputRowTitleWidth = function (width) {
    width -= this.getInnerPadding('left');

    var children = this.sizerChildren;
    for (var i = 0, cnt = children.length; i < cnt; i++) {
        var child = children[i];
        if (child.rexSizer.hidden) {
            continue;
        }

        if (child.setMinTitleWidth) {
            child.setMinTitleWidth(width);
        } else if (child.setInputRowTitleWidth) {
            child.setInputRowTitleWidth(width);
        }
    }
    return this;
}

export default SetInputRowTitleWidth;
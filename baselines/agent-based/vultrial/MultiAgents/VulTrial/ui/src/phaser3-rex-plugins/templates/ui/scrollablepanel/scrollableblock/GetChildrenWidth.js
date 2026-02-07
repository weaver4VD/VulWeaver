var GetChildrenWidth = function () {
    if (this.rexSizer.hidden) {
        return 0;
    }

    var result;
    var child = this.child,
        childConfig = child.rexSizer;
    if (childConfig.hidden) {
        result = 0;
    } else if (this.scrollMode === 0) {
        result = this.getChildWidth(child);
    } else {
        result = 0;
    }

    return result;
}

export default GetChildrenWidth;
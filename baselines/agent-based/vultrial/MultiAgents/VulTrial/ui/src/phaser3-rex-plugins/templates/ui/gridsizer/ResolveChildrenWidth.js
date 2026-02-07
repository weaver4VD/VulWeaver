var ResolveChildrenWidth = function (parentWidth) {
    var child, childWidth;
    var colWidth;
    for (var i in this.sizerChildren) {
        child = this.sizerChildren[i];
        if (child && child.isRexSizer && !child.ignoreLayout) {
            colWidth = this.getColumnWidth(parseInt(i) % this.columnCount);
            childWidth = this.getExpandedChildWidth(child, colWidth);
            childWidth = child.resolveWidth(childWidth);
            child.resolveChildrenWidth(childWidth);
        }
    }
}

export default ResolveChildrenWidth;
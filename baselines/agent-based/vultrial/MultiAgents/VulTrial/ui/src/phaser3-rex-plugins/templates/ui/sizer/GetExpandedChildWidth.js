var GetExpandedChildWidth = function (child, parentWidth) {
    if (parentWidth === undefined) {
        parentWidth = this.width;
    }

    var childWidth;
    var childConfig = child.rexSizer;
    var padding = childConfig.padding;
    if (this.orientation === 0) {
        if ((childConfig.proportion > 0) && (this.proportionLength > 0)) {
            childWidth = (childConfig.proportion * this.proportionLength);
        }
    } else {
        if (childConfig.expand) {
            var innerWidth = parentWidth - this.space.left - this.space.right;
            childWidth = innerWidth - padding.left - padding.right;
        }
    }
    return childWidth;
}

export default GetExpandedChildWidth;
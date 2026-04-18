var GetExpandedChildHeight = function (child, parentHeight) {
    if (parentHeight === undefined) {
        parentHeight = this.height;
    }

    var childHeight;
    var childConfig = child.rexSizer;
    var padding = childConfig.padding;
    if (this.orientation === 0) {
        if (childConfig.expand) {
            var innerHeight = parentHeight - this.space.top - this.space.bottom;
            childHeight = innerHeight - padding.top - padding.bottom;
        }
    } else {
        if ((childConfig.proportion > 0) && (this.proportionLength > 0)) {
            childHeight = (childConfig.proportion * this.proportionLength);
        }
    }
    return childHeight;
}

export default GetExpandedChildHeight;
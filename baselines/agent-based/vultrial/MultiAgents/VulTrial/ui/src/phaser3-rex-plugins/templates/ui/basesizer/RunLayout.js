var RunLayout = function (parent, newWidth, newHeight) {
    if (this.ignoreLayout) {
        return this;
    }

    var isTopmostParent = !parent;
    if (isTopmostParent) {
        this.preLayout();
    }
    newWidth = this.resolveWidth(newWidth);
    if (isTopmostParent) {
        this.resolveChildrenWidth(newWidth);
        this.runWidthWrap(newWidth);
    }
    newHeight = this.resolveHeight(newHeight);
    this.postResolveSize(newWidth, newHeight);
    this.resize(newWidth, newHeight);

    if (this.sizerEventsEnable) {
        if (this.layoutedChildren === undefined) {
            this.layoutedChildren = [];
        }
    }
    this.layoutChildren();
    this.layoutBackgrounds();

    if (this.sizerEventsEnable) {
        this.emit('postlayout', this.layoutedChildren, this);
        this.layoutedChildren.length = 0;
    }

    return this.postLayout();
}
export default RunLayout;
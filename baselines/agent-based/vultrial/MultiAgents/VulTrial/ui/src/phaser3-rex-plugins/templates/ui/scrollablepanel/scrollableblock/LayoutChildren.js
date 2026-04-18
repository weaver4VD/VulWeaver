import ResizeGameObject from '../../../../plugins/utils/size/ResizeGameObject.js';

var LayoutChildren = function () {
    var child = this.child;
    var childWidth, childHeight;
    if (!child.rexSizer.hidden) {
        if (this.scrollMode === 0) {
            childWidth = this.width;
        } else {
            childHeight = this.height;
        }
        if (child.isRexSizer) {
            child.runLayout(this, childWidth, childHeight);
        } else {
            ResizeGameObject(child, childWidth, childHeight);
        }
        this.resetChildPosition();
        this.layoutChildrenMask();
        this.maskChildren();
    }
}

export default LayoutChildren;
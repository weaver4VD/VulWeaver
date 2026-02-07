export default {
    getMaxInputRowTitleWidth() {
        var child = this.childrenMap.child;
        var titleWidth = child.getMaxInputRowTitleWidth();
        return titleWidth + this.getInnerPadding('left');
    },

    setInputRowTitleWidth(width) {
        width -= this.getInnerPadding('left');

        var child = this.childrenMap.child;
        child.setInputRowTitleWidth(width);
        return this;
    }
}
export default {
    setBindingTarget(target) {
        var child = this.childrenMap.child;
        child.setBindingTarget(target);
        return this;
    },
}
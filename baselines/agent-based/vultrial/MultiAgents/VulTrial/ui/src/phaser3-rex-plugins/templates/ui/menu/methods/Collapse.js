var Collapse = function () {
    var root = this.root;
    root.emit('collapse', this, this.parentButton, root);

    var duration = root.easeOut.duration;
    root.transitOutCallback(this, duration);
    this.collapseSubMenu();
    this.delayCall(duration, this.destroy, this);

    return this;
}

export default Collapse;
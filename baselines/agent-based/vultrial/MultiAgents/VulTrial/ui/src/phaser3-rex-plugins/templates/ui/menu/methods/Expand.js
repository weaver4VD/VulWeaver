var Expand = function () {
    var root = this.root;

    var duration = root.easeIn.duration;
    root.transitInCallback(this, duration);

    if (this !== this.root) {
        this.delayCall(duration, function () {
            this.root.emit('popup.complete', this);
        }, this);
    }
}

export default Expand;
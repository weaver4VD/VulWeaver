var ResolveHeight = function (height) {
    var minHeight = Math.max(this.childrenHeight, this.minHeight);
    if (height === undefined) {
        height = minHeight;
    } else {
        if (minHeight > height) {
        }
    }

    return height;
}

export default ResolveHeight;
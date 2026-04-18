var ResolveWidth = function (width) {
    if (width === undefined) {
        width = Math.max(this.childrenWidth, this.minWidth);
    } else {
        
    }

    return width;
}

export default ResolveWidth;
var ShrinkSizeByRatio = function (rectangle, maxRatio, minRatio) {
    var width = rectangle.width,
        height = rectangle.height,
        ratio = width / height;

    if ((maxRatio !== undefined) && (ratio > maxRatio)) {
        rectangle.width = height * maxRatio;
    }

    if ((minRatio !== undefined) && (ratio < minRatio)) {
        rectangle.height = width / minRatio;
    }

    return rectangle;
}

export default ShrinkSizeByRatio;
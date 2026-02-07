var GetPointPosition = function (quad) {
    var points;
    var top = 0, bottom = quad.height,
        left = 0, right = quad.width;
    if (quad.isNinePointMode) {
        var centerX = (left + right) / 2;
        var centerY = (top + bottom) / 2;
        points = [
            left, top,
            centerX, top,
            right, top,
            left, centerY,
            centerX, centerY,
            right, centerY,
            left, bottom,
            centerX, bottom,
            right, bottom
        ];
    } else {
        points = [
            left, top,
            right, top,
            left, bottom,
            right, bottom
        ];
    }

    return points;
}
export default GetPointPosition;
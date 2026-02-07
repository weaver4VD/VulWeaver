import Offset from './Offset.js';

var RingToTileXYArray = function (centerTileXY, radius, out) {
    if (out === undefined) {
        out = [];
    }

    var i, j;
    i = radius;
    for (j = -radius; j <= radius; j++) {
        out.push(Offset(centerTileXY, i, j));
    }
    j = radius;
    for (i = radius - 1; i >= -radius; i--) {
        out.push(Offset(centerTileXY, i, j));
    }
    i = -radius;
    for (j = radius - 1; j >= -radius; j--) {
        out.push(Offset(centerTileXY, i, j));
    }
    j = -radius;
    for (i = -radius + 1; i <= radius - 1; i++) {
        out.push(Offset(centerTileXY, i, j));
    }

    return out;
}
export default RingToTileXYArray;
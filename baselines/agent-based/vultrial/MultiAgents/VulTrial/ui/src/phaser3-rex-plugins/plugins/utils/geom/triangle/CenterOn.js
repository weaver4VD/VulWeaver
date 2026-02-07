

import Centroid from './Centroid.js';
import Offset from './Offset.js';




var CenterOn = function (triangle, x, y, centerFunc) {
    if (centerFunc === undefined) { centerFunc = Centroid; }
    var center = centerFunc(triangle);
    var diffX = x - center.x;
    var diffY = y - center.y;

    return Offset(triangle, diffX, diffY);
};

export default CenterOn;

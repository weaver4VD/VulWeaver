

import Point from '../point/Point.js';


var Centroid = function (triangle, out) {
    if (out === undefined) { out = new Point(); }

    out.x = (triangle.x1 + triangle.x2 + triangle.x3) / 3;
    out.y = (triangle.y1 + triangle.y2 + triangle.y3) / 3;

    return out;
};

export default Centroid;

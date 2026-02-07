

import Point from '../point/Point.js';


var GetPoint = function (line, position, out) {
    if (out === undefined) { out = new Point(); }

    out.x = line.x1 + (line.x2 - line.x1) * position;
    out.y = line.y1 + (line.y2 - line.y1) * position;

    return out;
};

export default GetPoint;

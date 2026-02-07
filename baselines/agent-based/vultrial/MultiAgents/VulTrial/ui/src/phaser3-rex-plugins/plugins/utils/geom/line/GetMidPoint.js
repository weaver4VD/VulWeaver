

import Point from '../point/Point.js';


var GetMidPoint = function (line, out) {
    if (out === undefined) { out = new Point(); }

    out.x = (line.x1 + line.x2) / 2;
    out.y = (line.y1 + line.y2) / 2;

    return out;
};

export default GetMidPoint;



import Point from '../point/Point.js';


var GetCenter = function (rect, out) {
    if (out === undefined) { out = new Point(); }

    out.x = rect.centerX;
    out.y = rect.centerY;

    return out;
};

export default GetCenter;

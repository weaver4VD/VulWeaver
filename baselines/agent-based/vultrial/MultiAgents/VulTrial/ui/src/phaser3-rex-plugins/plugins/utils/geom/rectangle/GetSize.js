

import Point from '../point/Point.js';



var GetSize = function (rect, out) {
    if (out === undefined) { out = new Point(); }

    out.x = rect.width;
    out.y = rect.height;

    return out;
};

export default GetSize;

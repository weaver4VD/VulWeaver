

import Point from './Point.js';


var Negative = function (point, out) {
    if (out === undefined) { out = new Point(); }

    return out.setTo(-point.x, -point.y);
};

export default Negative;

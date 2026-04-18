

import Point from '../point/Point.js';


var Random = function (rect, out) {
    if (out === undefined) { out = new Point(); }

    out.x = rect.x + (Math.random() * rect.width);
    out.y = rect.y + (Math.random() * rect.height);

    return out;
};

export default Random;

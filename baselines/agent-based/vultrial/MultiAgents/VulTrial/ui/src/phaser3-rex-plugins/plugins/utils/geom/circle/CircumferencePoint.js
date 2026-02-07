

import Point from '../point/Point.js';


var CircumferencePoint = function (circle, angle, out) {
    if (out === undefined) { out = new Point(); }

    out.x = circle.x + (circle.radius * Math.cos(angle));
    out.y = circle.y + (circle.radius * Math.sin(angle));

    return out;
};

export default CircumferencePoint;

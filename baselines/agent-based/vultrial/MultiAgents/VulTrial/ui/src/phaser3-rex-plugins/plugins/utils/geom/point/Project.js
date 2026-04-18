

import Point from './Point.js';
import GetMagnitudeSq from './GetMagnitudeSq.js';


var Project = function (pointA, pointB, out) {
    if (out === undefined) { out = new Point(); }

    var dot = ((pointA.x * pointB.x) + (pointA.y * pointB.y));
    var amt = dot / GetMagnitudeSq(pointB);

    if (amt !== 0) {
        out.x = amt * pointB.x;
        out.y = amt * pointB.y;
    }

    return out;
};

export default Project;

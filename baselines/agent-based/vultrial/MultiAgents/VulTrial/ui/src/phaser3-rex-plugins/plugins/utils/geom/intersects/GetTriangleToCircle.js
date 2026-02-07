

import GetLineToCircle from './GetLineToCircle.js';
import TriangleToCircle from './TriangleToCircle.js';


var GetTriangleToCircle = function (triangle, circle, out) {
    if (out === undefined) { out = []; }

    if (TriangleToCircle(triangle, circle)) {
        var lineA = triangle.getLineA();
        var lineB = triangle.getLineB();
        var lineC = triangle.getLineC();

        GetLineToCircle(lineA, circle, out);
        GetLineToCircle(lineB, circle, out);
        GetLineToCircle(lineC, circle, out);
    }

    return out;
};

export default GetTriangleToCircle;

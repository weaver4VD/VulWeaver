

import TriangleToTriangle from './TriangleToTriangle.js';
import GetTriangleToLine from './GetTriangleToLine.js';


var GetTriangleToTriangle = function (triangleA, triangleB, out) {
    if (out === undefined) { out = []; }

    if (TriangleToTriangle(triangleA, triangleB)) {
        var lineA = triangleB.getLineA();
        var lineB = triangleB.getLineB();
        var lineC = triangleB.getLineC();

        GetTriangleToLine(triangleA, lineA, out);
        GetTriangleToLine(triangleA, lineB, out);
        GetTriangleToLine(triangleA, lineC, out);
    }

    return out;
};

export default GetTriangleToTriangle;

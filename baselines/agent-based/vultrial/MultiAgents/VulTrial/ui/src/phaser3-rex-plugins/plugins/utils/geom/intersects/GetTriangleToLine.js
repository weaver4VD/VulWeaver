

import Point from '../point/Point.js';
import TriangleToLine from './TriangleToLine.js';
import LineToLine from './LineToLine.js';


var GetTriangleToLine = function (triangle, line, out) {
    if (out === undefined) { out = []; }

    if (TriangleToLine(triangle, line)) {
        var lineA = triangle.getLineA();
        var lineB = triangle.getLineB();
        var lineC = triangle.getLineC();

        var output = [new Point(), new Point(), new Point()];

        var result = [
            LineToLine(lineA, line, output[0]),
            LineToLine(lineB, line, output[1]),
            LineToLine(lineC, line, output[2])
        ];

        for (var i = 0; i < 3; i++) {
            if (result[i]) { out.push(output[i]); }
        }
    }

    return out;
};

export default GetTriangleToLine;

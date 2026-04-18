

import Point from '../point/Point.js';
import LineToLine from './LineToLine.js';
import LineToRectangle from './LineToRectangle.js';


var GetLineToRectangle = function (line, rect, out) {
    if (out === undefined) { out = []; }

    if (LineToRectangle(line, rect)) {
        var lineA = rect.getLineA();
        var lineB = rect.getLineB();
        var lineC = rect.getLineC();
        var lineD = rect.getLineD();

        var output = [new Point(), new Point(), new Point(), new Point()];

        var result = [
            LineToLine(lineA, line, output[0]),
            LineToLine(lineB, line, output[1]),
            LineToLine(lineC, line, output[2]),
            LineToLine(lineD, line, output[3])
        ];

        for (var i = 0; i < 4; i++) {
            if (result[i]) { out.push(output[i]); }
        }
    }

    return out;
};

export default GetLineToRectangle;

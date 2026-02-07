

import Contains from '../triangle/Contains.js';
import LineToLine from './LineToLine.js';


var TriangleToLine = function (triangle, line) {
    if (Contains(triangle, line.getPointA()) || Contains(triangle, line.getPointB())) {
        return true;
    }
    if (LineToLine(triangle.getLineA(), line)) {
        return true;
    }

    if (LineToLine(triangle.getLineB(), line)) {
        return true;
    }

    if (LineToLine(triangle.getLineC(), line)) {
        return true;
    }

    return false;
};

export default TriangleToLine;

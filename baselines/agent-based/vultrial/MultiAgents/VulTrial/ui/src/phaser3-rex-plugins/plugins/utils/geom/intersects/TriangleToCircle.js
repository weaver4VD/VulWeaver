

import LineToCircle from './LineToCircle.js';
import Contains from '../triangle/Contains.js';


var TriangleToCircle = function (triangle, circle) {

    if (
        triangle.left > circle.right ||
        triangle.right < circle.left ||
        triangle.top > circle.bottom ||
        triangle.bottom < circle.top) {
        return false;
    }

    if (Contains(triangle, circle.x, circle.y)) {
        return true;
    }

    if (LineToCircle(triangle.getLineA(), circle)) {
        return true;
    }

    if (LineToCircle(triangle.getLineB(), circle)) {
        return true;
    }

    if (LineToCircle(triangle.getLineC(), circle)) {
        return true;
    }

    return false;
};

export default TriangleToCircle;

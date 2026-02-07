import InitPoints from '../utils/InitPoints.js';

var SetPoints = function (x, y, width, height, type, points) {
    if (points === undefined) {
        points = InitPoints(4);
    }

    var halfW = width / 2;
    var halfH = height / 2;

    if (type === 0) {
        points[0].x = x + halfW;
        points[0].y = y - halfH;
        points[1].x = x + halfW;
        points[1].y = y + halfH;
        points[2].x = x - halfW;
        points[2].y = y + halfH;
        points[3].x = x - halfW;
        points[3].y = y - halfH;
    } else {
        points[0].x = x + halfW;
        points[0].y = y;
        points[1].x = x;
        points[1].y = y + halfH;
        points[2].x = x - halfW;
        points[2].y = y;
        points[3].x = x;
        points[3].y = y - halfH;
    }
    return points;
}

export default SetPoints;
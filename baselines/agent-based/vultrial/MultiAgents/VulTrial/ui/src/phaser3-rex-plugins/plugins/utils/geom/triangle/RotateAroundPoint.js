

import RotateAroundXY from './RotateAroundXY.js';


var RotateAroundPoint = function (triangle, point, angle) {
    return RotateAroundXY(triangle, point.x, point.y, angle);
};

export default RotateAroundPoint;

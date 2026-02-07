

import RotateAroundXY from './RotateAroundXY.js';


var RotateAroundPoint = function (line, point, angle) {
    return RotateAroundXY(line, point.x, point.y, angle);
};

export default RotateAroundPoint;

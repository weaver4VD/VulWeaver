

import RotateAroundXY from './RotateAroundXY.js';


var Rotate = function (line, angle) {
    var x = (line.x1 + line.x2) / 2;
    var y = (line.y1 + line.y2) / 2;

    return RotateAroundXY(line, x, y, angle);
};

export default Rotate;

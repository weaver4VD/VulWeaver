

import RotateAroundXY from './RotateAroundXY.js';
import InCenter from './InCenter.js';


var Rotate = function (triangle, angle) {
    var point = InCenter(triangle);

    return RotateAroundXY(triangle, point.x, point.y, angle);
};

export default Rotate;

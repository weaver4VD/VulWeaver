

import Contains from './Contains.js';


var ContainsPoint = function (polygon, point) {
    return Contains(polygon, point.x, point.y);
};

export default ContainsPoint;

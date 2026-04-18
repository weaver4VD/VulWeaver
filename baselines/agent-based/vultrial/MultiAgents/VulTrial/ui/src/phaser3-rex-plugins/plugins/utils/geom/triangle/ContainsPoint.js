

import Contains from './Contains.js';


var ContainsPoint = function (triangle, point) {
    return Contains(triangle, point.x, point.y);
};

export default ContainsPoint;

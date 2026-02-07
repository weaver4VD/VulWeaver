

import Contains from './Contains.js';


var ContainsPoint = function (circle, point) {
    return Contains(circle, point.x, point.y);
};

export default ContainsPoint;

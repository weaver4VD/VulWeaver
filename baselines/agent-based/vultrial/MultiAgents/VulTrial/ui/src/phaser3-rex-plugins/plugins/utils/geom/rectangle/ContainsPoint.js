

import Contains from './Contains.js';


var ContainsPoint = function (rect, point) {
    return Contains(rect, point.x, point.y);
};

export default ContainsPoint;

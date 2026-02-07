

import Contains from './Contains.js';


var ContainsPoint = function (ellipse, point) {
    return Contains(ellipse, point.x, point.y);
};

export default ContainsPoint;

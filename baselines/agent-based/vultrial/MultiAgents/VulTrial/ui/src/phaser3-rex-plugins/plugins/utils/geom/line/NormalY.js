

import MATH_CONST from '../../math/const.js';
import Angle from './Angle.js';


var NormalY = function (line) {
    return Math.sin(Angle(line) - MATH_CONST.TAU);
};

export default NormalY;

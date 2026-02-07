

import MATH_CONST from '../../math/const.js';
import Angle from './Angle.js';


var NormalX = function (line) {
    return Math.cos(Angle(line) - MATH_CONST.TAU);
};

export default NormalX;



import MATH_CONST from '../../math/const.js';
import Wrap from '../../math/Wrap.js';
import Angle from './Angle.js';


var NormalAngle = function (line) {
    var angle = Angle(line) - MATH_CONST.TAU;

    return Wrap(angle, -Math.PI, Math.PI);
};

export default NormalAngle;

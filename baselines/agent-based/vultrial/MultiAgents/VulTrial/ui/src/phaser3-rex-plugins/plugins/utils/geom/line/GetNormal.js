

import MATH_CONST from '../../math/const.js';
import Angle from './Angle.js';
import Point from '../point/Point.js';


var GetNormal = function (line, out) {
    if (out === undefined) { out = new Point(); }

    var a = Angle(line) - MATH_CONST.TAU;

    out.x = Math.cos(a);
    out.y = Math.sin(a);

    return out;
};

export default GetNormal;

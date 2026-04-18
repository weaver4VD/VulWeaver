

import CircumferencePoint from './CircumferencePoint.js';
import FromPercent from '../../math/FromPercent.js';
import MATH_CONST from '../../math/const.js';
import Point from '../point/Point.js';


var GetPoint = function (ellipse, position, out) {
    if (out === undefined) { out = new Point(); }

    var angle = FromPercent(position, 0, MATH_CONST.PI2);

    return CircumferencePoint(ellipse, angle, out);
};

export default GetPoint;

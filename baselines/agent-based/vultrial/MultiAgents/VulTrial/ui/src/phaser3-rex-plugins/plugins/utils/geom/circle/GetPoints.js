

import Circumference from './Circumference.js';
import CircumferencePoint from './CircumferencePoint.js';
import FromPercent from '../../math/FromPercent.js';
import MATH_CONST from '../../math/const.js';


var GetPoints = function (circle, quantity, stepRate, out) {
    if (out === undefined) { out = []; }
    if (!quantity) {
        quantity = Circumference(circle) / stepRate;
    }

    for (var i = 0; i < quantity; i++) {
        var angle = FromPercent(i / quantity, 0, MATH_CONST.PI2);

        out.push(CircumferencePoint(circle, angle));
    }

    return out;
};

export default GetPoints;

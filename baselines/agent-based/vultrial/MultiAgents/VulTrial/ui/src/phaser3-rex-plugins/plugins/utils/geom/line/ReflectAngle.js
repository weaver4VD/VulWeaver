

import Angle from './Angle.js';
import NormalAngle from './NormalAngle.js';


var ReflectAngle = function (lineA, lineB) {
    return (2 * NormalAngle(lineB) - Math.PI - Angle(lineA));
};

export default ReflectAngle;

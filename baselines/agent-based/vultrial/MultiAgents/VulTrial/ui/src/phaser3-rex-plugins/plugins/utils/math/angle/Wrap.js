

import MathWrap from '../Wrap.js';


var Wrap = function (angle) {
    return MathWrap(angle, -Math.PI, Math.PI);
};

export default Wrap;

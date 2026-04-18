

import SmoothStep from '../SmoothStep.js';


var SmoothStepInterpolation = function (t, min, max) {
    return min + (max - min) * SmoothStep(t, 0, 1);
};

export default SmoothStepInterpolation;

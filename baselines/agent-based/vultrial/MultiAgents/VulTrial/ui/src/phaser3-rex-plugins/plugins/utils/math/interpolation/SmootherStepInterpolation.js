

import SmootherStep from '../SmootherStep.js';


var SmootherStepInterpolation = function (t, min, max) {
    return min + (max - min) * SmootherStep(t, 0, 1);
};

export default SmootherStepInterpolation;

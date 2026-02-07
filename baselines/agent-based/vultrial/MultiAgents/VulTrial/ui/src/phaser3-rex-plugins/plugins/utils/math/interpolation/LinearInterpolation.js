

import Linear from '../Linear.js';


var LinearInterpolation = function (v, k) {
    var m = v.length - 1;
    var f = m * k;
    var i = Math.floor(f);

    if (k < 0) {
        return Linear(v[0], v[1], f);
    }
    else if (k > 1) {
        return Linear(v[m], v[m - 1], m - f);
    }
    else {
        return Linear(v[i], v[(i + 1 > m) ? m : i + 1], f - i);
    }
};

export default LinearInterpolation;

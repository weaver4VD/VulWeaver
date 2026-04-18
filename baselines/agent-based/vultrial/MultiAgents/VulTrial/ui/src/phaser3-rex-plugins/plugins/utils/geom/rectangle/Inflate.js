

import CenterOn from './CenterOn.js';



var Inflate = function (rect, x, y) {
    var cx = rect.centerX;
    var cy = rect.centerY;

    rect.setSize(rect.width + (x * 2), rect.height + (y * 2));

    return CenterOn(rect, cx, cy);
};

export default Inflate;

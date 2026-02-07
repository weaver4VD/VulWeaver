

import Rectangle from '../rectangle/Rectangle.js';


var GetBounds = function (ellipse, out) {
    if (out === undefined) { out = new Rectangle(); }

    out.x = ellipse.left;
    out.y = ellipse.top;
    out.width = ellipse.width;
    out.height = ellipse.height;

    return out;
};

export default GetBounds;

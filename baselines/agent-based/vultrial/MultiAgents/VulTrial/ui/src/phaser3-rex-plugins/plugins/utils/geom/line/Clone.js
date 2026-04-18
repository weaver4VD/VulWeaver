

import Line from './Line.js';


var Clone = function (source) {
    return new Line(source.x1, source.y1, source.x2, source.y2);
};

export default Clone;

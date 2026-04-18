

import Triangle from './Triangle.js';


var Clone = function (source) {
    return new Triangle(source.x1, source.y1, source.x2, source.y2, source.x3, source.y3);
};

export default Clone;



import Point from './Point.js';


var Clone = function (source) {
    return new Point(source.x, source.y);
};

export default Clone;



import Rectangle from './Rectangle.js';


var Clone = function (source) {
    return new Rectangle(source.x, source.y, source.width, source.height);
};

export default Clone;

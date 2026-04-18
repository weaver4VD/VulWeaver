

import Ellipse from './Ellipse.js';


var Clone = function (source) {
    return new Ellipse(source.x, source.y, source.width, source.height);
};

export default Clone;

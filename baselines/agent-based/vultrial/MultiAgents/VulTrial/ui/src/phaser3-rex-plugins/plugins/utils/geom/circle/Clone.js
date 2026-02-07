

import Circle from './Circle.js';


var Clone = function (source) {
    return new Circle(source.x, source.y, source.radius);
};

export default Clone;

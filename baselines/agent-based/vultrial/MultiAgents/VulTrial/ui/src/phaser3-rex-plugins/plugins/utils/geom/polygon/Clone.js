

import Polygon from './Polygon.js';


var Clone = function (polygon) {
    return new Polygon(polygon.points);
};

export default Clone;

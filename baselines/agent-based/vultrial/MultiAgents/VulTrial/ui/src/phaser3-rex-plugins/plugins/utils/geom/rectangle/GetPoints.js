

import GetPoint from './GetPoint.js';
import Perimeter from './Perimeter.js';


var GetPoints = function (rectangle, quantity, stepRate, out) {
    if (out === undefined) { out = []; }
    if (!quantity) {
        quantity = Perimeter(rectangle) / stepRate;
    }

    for (var i = 0; i < quantity; i++) {
        var position = i / quantity;

        out.push(GetPoint(rectangle, position));
    }

    return out;
};

export default GetPoints;

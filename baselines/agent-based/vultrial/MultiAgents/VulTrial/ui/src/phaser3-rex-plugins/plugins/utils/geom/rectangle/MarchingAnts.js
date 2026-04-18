

import Perimeter from './Perimeter.js';
import Point from '../point/Point.js';



var MarchingAnts = function (rect, step, quantity, out) {
    if (out === undefined) { out = []; }

    if (!step && !quantity) {
        return out;
    }
    if (!step) {
        step = Perimeter(rect) / quantity;
    }
    else {
        quantity = Math.round(Perimeter(rect) / step);
    }

    var x = rect.x;
    var y = rect.y;
    var face = 0;

    for (var i = 0; i < quantity; i++) {
        out.push(new Point(x, y));

        switch (face) {
            case 0:
                x += step;

                if (x >= rect.right) {
                    face = 1;
                    y += (x - rect.right);
                    x = rect.right;
                }
                break;
            case 1:
                y += step;

                if (y >= rect.bottom) {
                    face = 2;
                    x -= (y - rect.bottom);
                    y = rect.bottom;
                }
                break;
            case 2:
                x -= step;

                if (x <= rect.left) {
                    face = 3;
                    y -= (rect.left - x);
                    x = rect.left;
                }
                break;
            case 3:
                y -= step;

                if (y <= rect.top) {
                    face = 0;
                    y = rect.top;
                }
                break;
        }
    }

    return out;
};

export default MarchingAnts;

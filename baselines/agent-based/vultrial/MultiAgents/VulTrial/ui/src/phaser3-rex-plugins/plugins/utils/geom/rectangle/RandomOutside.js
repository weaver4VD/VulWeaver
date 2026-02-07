

import Between from '../../math/Between.js';
import ContainsRect from './ContainsRect.js';
import Point from '../point/Point.js';


var RandomOutside = function (outer, inner, out) {
    if (out === undefined) { out = new Point(); }

    if (ContainsRect(outer, inner)) {

        switch (Between(0, 3)) {
            case 0:
                out.x = outer.x + (Math.random() * (inner.right - outer.x));
                out.y = outer.y + (Math.random() * (inner.top - outer.y));
                break;

            case 1:
                out.x = inner.x + (Math.random() * (outer.right - inner.x));
                out.y = inner.bottom + (Math.random() * (outer.bottom - inner.bottom));
                break;

            case 2:
                out.x = outer.x + (Math.random() * (inner.x - outer.x));
                out.y = inner.y + (Math.random() * (outer.bottom - inner.y));
                break;

            case 3:
                out.x = inner.right + (Math.random() * (outer.right - inner.right));
                out.y = outer.y + (Math.random() * (inner.bottom - outer.y));
                break;
        }
    }

    return out;
};

export default RandomOutside;

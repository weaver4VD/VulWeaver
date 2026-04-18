

import GetLineToCircle from './GetLineToCircle.js';
import CircleToRectangle from './CircleToRectangle.js';


var GetCircleToRectangle = function (circle, rect, out)
{
    if (out === undefined) { out = []; }

    if (CircleToRectangle(circle, rect))
    {
        var lineA = rect.getLineA();
        var lineB = rect.getLineB();
        var lineC = rect.getLineC();
        var lineD = rect.getLineD();

        GetLineToCircle(lineA, circle, out);
        GetLineToCircle(lineB, circle, out);
        GetLineToCircle(lineC, circle, out);
        GetLineToCircle(lineD, circle, out);
    }

    return out;
};

export default GetCircleToRectangle;

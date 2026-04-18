

import Point from '../point/Point';


var LineToLine = function (line1, line2, out) {
    if (out === undefined) { out = new Point(); }

    var x1 = line1.x1;
    var y1 = line1.y1;
    var x2 = line1.x2;
    var y2 = line1.y2;

    var x3 = line2.x1;
    var y3 = line2.y1;
    var x4 = line2.x2;
    var y4 = line2.y2;

    var numA = (x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3);
    var numB = (x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3);
    var deNom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1);

    if (deNom === 0) {
        return false;
    }

    var uA = numA / deNom;
    var uB = numB / deNom;

    if (uA >= 0 && uA <= 1 && uB >= 0 && uB <= 1) {
        out.x = x1 + (uA * (x2 - x1));
        out.y = y1 + (uA * (y2 - y1));

        return true;
    }

    return false;
};

export default LineToLine;

import GetLineToPoints from './GetLineToPoints.js';
import Clone from '../../utils/object/Clone.js';

const GetAABB = Phaser.Geom.Polygon.GetAABB;
const LineToRectangle = Phaser.Geom.Intersects.LineToRectangle;

var GetLineToPolygon = function (line, polygons, out) {
    if (out === undefined) {
        out = {};
    } else if (out === true) {
        out = globResult;
    }
    

    if (!Array.isArray(polygons)) {
        polygons = [polygons];
    }

    var closestIntersect = false;
    out.d = Infinity;

    for (var i = 0; i < polygons.length; i++) {
        var polygon = polygons[i];
        if ((polygon.points.length > 9) &&
            !LineToRectangle(line, GetAABB(polygon, AABBRect))) {
            continue;
        }

        var intersectionResult = GetLineToPoints(line, polygon.points, true);
        if (intersectionResult) {
            if (intersectionResult.d < out.d) {
                Clone(intersectionResult, out);
                out.shapeIndex = i;

                closestIntersect = true;
            }
        }
    }

    return (closestIntersect) ? out : null;
};

var globResult = {};
var AABBRect = new Phaser.Geom.Rectangle();

export default GetLineToPolygon;

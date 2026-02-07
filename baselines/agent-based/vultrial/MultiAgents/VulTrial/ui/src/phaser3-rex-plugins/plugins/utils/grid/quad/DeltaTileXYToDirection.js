
import {
    OrthogonalMap
} from './DistanceToDeltaTileXY.js';

var ReverseDirMap = function (dirMap) {
    var out = {},
        entry, x, y;
    for (var dir in dirMap) {
        entry = dirMap[dir];
        x = entry[0];
        y = entry[1];
        if (!out.hasOwnProperty(x)) {
            out[x] = {}
        }
        out[x][y] = parseInt(dir);
    }
    return out;
}

const OrthogonalMapOut = ReverseDirMap(OrthogonalMap);
const IsometricMapOut = OrthogonalMapOut;

export {
    OrthogonalMapOut as OrthogonalMap,
    IsometricMapOut as IsometricMap
};
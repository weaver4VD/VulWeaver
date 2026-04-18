
import DirectionToDeltaTileXY from './DirectionToDeltaTileXY.js';

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

const Neighbors = [
    [
        ReverseDirMap(DirectionToDeltaTileXY[0][0]),
        ReverseDirMap(DirectionToDeltaTileXY[0][1])
    ],
    [
        ReverseDirMap(DirectionToDeltaTileXY[1][0]),
        ReverseDirMap(DirectionToDeltaTileXY[1][1])
    ],
    [
        ReverseDirMap(DirectionToDeltaTileXY[2][0]),
        ReverseDirMap(DirectionToDeltaTileXY[2][1])
    ],
    [
        ReverseDirMap(DirectionToDeltaTileXY[3][0]),
        ReverseDirMap(DirectionToDeltaTileXY[3][1])
    ]
];

export default Neighbors;
var Rotate = function (direction, chessTileXYZMap, out) {
    if (direction === undefined) {
        direction = 0;
    }
    if (chessTileXYZMap === undefined) {
        chessTileXYZMap = this.tileXYZMap;
    }
    if (out === undefined) {
        out = {};
    }
    var chessTileXYZ, newTileXYZ;
    for (var uid in chessTileXYZMap) {
        chessTileXYZ = chessTileXYZMap[uid];
        newTileXYZ = this.board.rotate(chessTileXYZ, direction);
        newTileXYZ.z = chessTileXYZ.z;
        out[uid] = newTileXYZ;
    }
    return out;
}

export default Rotate;
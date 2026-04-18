var Offset = function (tileX, tileY, chessTileXYZMap, out) {
    if (chessTileXYZMap === undefined) {
        chessTileXYZMap = this.tileXYZMap;
    }
    if (out === undefined) {
        out = {};
    }
    var chessTileXYZ, newTileXYZ;
    for (var uid in chessTileXYZMap) {
        chessTileXYZ = chessTileXYZMap[uid];
        newTileXYZ = this.board.offset(chessTileXYZ, tileX, tileY);
        newTileXYZ.z = chessTileXYZ.z;
        out[uid] = newTileXYZ;
    }
    return out;
}

export default Offset;
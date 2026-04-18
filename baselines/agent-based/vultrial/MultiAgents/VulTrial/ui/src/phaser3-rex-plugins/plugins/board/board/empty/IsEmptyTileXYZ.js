var IsEmptyTileXYZ = function (tileX, tileY, tileZ) {
    return this.contains(tileX, tileY) && !this.contains(tileX, tileY, tileZ);
}

export default IsEmptyTileXYZ;
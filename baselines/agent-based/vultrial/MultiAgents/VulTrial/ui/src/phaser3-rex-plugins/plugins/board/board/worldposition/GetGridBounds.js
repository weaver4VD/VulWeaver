var GetGridBounds = function (tileX, tileY, out) {
    if (tileX && (typeof (tileX) !== 'number')) {
        out = tileY;
        var tileXY = this.chessToTileXYZ(tileX);
        tileX = tileXY.x;
        tileY = tileXY.y;
    }
    return this.grid.getBounds(tileX, tileY, out);
}

export default GetGridBounds;
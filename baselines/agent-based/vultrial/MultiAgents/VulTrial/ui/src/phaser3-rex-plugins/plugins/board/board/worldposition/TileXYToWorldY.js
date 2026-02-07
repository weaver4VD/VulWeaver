var TileXYToWorldY = function (tileX, tileY) {
    return this.tileXYToWorldXY(tileX, tileY, true).y;
}
export default TileXYToWorldY;
var TileXYToWorldX = function (tileX, tileY) {
    return this.tileXYToWorldXY(tileX, tileY, true).x;
}
export default TileXYToWorldX;
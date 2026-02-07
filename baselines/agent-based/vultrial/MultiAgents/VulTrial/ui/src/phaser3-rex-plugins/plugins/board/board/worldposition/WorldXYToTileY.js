var WorldXYToTileY = function (worldX, worldY) {
    return this.worldXYToTileXY(worldX, worldY, true).y;
}
export default WorldXYToTileY;
var WorldXYToTileX = function (worldX, worldY) {
    return this.worldXYToTileXY(worldX, worldY, true).x;
}
export default WorldXYToTileX;
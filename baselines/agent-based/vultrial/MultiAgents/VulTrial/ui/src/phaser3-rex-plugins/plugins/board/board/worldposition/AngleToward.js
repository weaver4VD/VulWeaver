var AngleToward = function (tileXY, direction) {
    if (tileXY === undefined) {
        tileXY = zeroTileXY;
    }
    var wrapModeSave = this.wrapMode;
    var infinityModeSave = this.infinityMode;
    this.wrapMode = false;
    this.infinityMode = true;
    var neighborTileXY = this.getNeighborTileXY(tileXY, direction, true);
    this.wrapMode = wrapModeSave;
    this.infinityMode = infinityModeSave;
    return this.angleBetween(tileXY, neighborTileXY);
}

var zeroTileXY = { x: 0, y: 0 };

export default AngleToward;
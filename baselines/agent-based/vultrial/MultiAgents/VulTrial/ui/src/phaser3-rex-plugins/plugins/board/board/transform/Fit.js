var Fit = function (tileXYArray) {
    var minX = Infinity;
    var minY = Infinity;
    var tileXY;
    for (var i in tileXYArray) {
        tileXY = tileXYArray[i];
        minX = Math.min(minX, tileXY.x);
        minY = Math.min(minY, tileXY.y);
    }
    if ((minX !== 0) || (minY !== 0)) {
        for (var i in tileXYArray) {
            tileXY = tileXYArray[i];
            this.offset(tileXY, -minX, -minY, tileXY);
        }
    }
    var maxX = -Infinity;
    var maxY = -Infinity;
    for (var i in tileXYArray) {
        tileXY = tileXYArray[i];
        maxX = Math.max(maxX, tileXY.x);
        maxY = Math.max(maxY, tileXY.y);
    }
    this.setBoardWidth(maxX + 1);
    this.setBoardHeight(maxY + 1);
    return tileXYArray;
}
export default Fit;
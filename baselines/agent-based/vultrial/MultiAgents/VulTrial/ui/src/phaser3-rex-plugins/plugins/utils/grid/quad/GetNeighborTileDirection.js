import {
    OrthogonalMap,
    IsometricMap
} from './DeltaTileXYToDirection.js';

var GetNeighborTileDirection = function (srcTileXY, neighborTileXY) {
    var deltaTileXYToDirMap
    switch (this.mode) {
        case 0:
            deltaTileXYToDirMap = OrthogonalMap;
            break;
        case 1:
            deltaTileXYToDirMap = IsometricMap;
            break;
        case 2:
            break;
    }

    var deltaTileX = neighborTileXY.x - srcTileXY.x;
    var deltaTileY = neighborTileXY.y - srcTileXY.y;    
    if (deltaTileXYToDirMap.hasOwnProperty(deltaTileX)) {
        var xEntry = deltaTileXYToDirMap[deltaTileX]
        if (xEntry.hasOwnProperty(deltaTileY)) {
            return xEntry[deltaTileY];
        }
    }
    return null;
}
export default GetNeighborTileDirection;
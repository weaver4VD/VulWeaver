

import RefreshSymbolCache from './match/RefreshSymbolCache.js';
import AnyMatch from './match/AnyMatch.js';

var PreTest = function () {
    var match = this.match;
    var directions = this.board.grid.halfDirections;
    var tileB;
    RefreshSymbolCache.call(this);
    for (var tileY = (this.board.height / 2), rowCnt = this.board.height; tileY < rowCnt; tileY++) {
        for (var tileX = 0, colCnt = this.board.width; tileX < colCnt; tileX++) {
            tileA.x = tileX;
            tileA.y = tileY;
            for (var dir = 0, dirCnt = directions.length; dir < dirCnt; dir++) {
                tileB = this.board.getNeighborTileXY(tileA, dir);
                swapSymbols(match, tileA, tileB);
                this.preTestResult = AnyMatch.call(this, 3);
                swapSymbols(match, tileA, tileB);

                if (this.preTestResult) {
                    return true;
                }
            }
        }
    }
    return false;
}

var swapSymbols = function (match, tileA, tileB) {
    var symbolA = match.getSymbol(tileA.x, tileA.y);
    var symbolB = match.getSymbol(tileB.x, tileB.y);
    match.setSymbol(tileA.x, tileA.y, symbolB);
    match.setSymbol(tileB.x, tileB.y, symbolA);
};

var tileA = {
    x: 0,
    y: 0
};

export default PreTest;


import RefreshSymbolCache from './match/RefreshSymbolCache.js';
import GetMatchN from './match/GetMatchN.js';
import RandomSymbol from './chess/RandomSymobl.js';

const GetRandom = Phaser.Utils.Array.GetRandom;

var BreakMatch3 = function () {
    var tileZ = this.chessTileZ,
        scope = this.chessCallbackScope,
        symbols = this.candidateSymbols;

    RefreshSymbolCache.call(this);
    GetMatchN.call(this, 3, function (result, board) {
        var tileXY = GetRandom(result.tileXY);
        var chess = board.tileXYZToChess(tileXY.x, tileXY.y, tileZ);
        var neighborChess = board.getNeighborChess(chess, null);
        var excluded = [];
        for (var i = 0, cnt = neighborChess.length; i < cnt; i++) {
            excluded.push(neighborChess[i].getData('symbol'));
        }
        var newSymbol = RandomSymbol(board, tileXY.x, tileXY.y, symbols, scope, excluded);
        if (newSymbol != null) {
            chess.setData('symbol', newSymbol);
        }
    });
}

export default BreakMatch3;
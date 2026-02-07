const GetRandom = Phaser.Utils.Array.GetRandom;

var RandomSymbol = function (board, tileX, tileY, callback, scope, excluded) {
    var symbol;
    if (Array.isArray(callback)) {
        var symbols = callback;
        if (excluded !== undefined) {
            for (var i = 0, cnt = symbols.length; i < cnt; i++) {
                symbol = symbols[i];
                if (excluded.indexOf(symbol) !== -1) {
                    continue;
                }
                tmpSymbolArray.push(symbol);
            }
            symbol = GetRandom(tmpSymbolArray);
            tmpSymbolArray.length = 0;
        } else {
            symbol = GetRandom(symbols);
        }

    } else if (typeof (obj) === 'function') {
        if (scope) {
            symbol = callback.call(scope, board, tileX, tileY, excluded);
        } else {
            symbol = callback(board, tileX, tileY, excluded);
        }
    } else {
        symbol = callback;
    }
    return symbol;
}

var tmpSymbolArray = [];
export default RandomSymbol;
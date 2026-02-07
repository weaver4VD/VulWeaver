import RandomSymbol from './RandomSymobl.js';

var CreateChess = function (tileX, tileY, symbols) {
    var scene = this.scene,
        board = this.board,
        scope = this.chessCallbackScope;
    var symbol = RandomSymbol(board, tileX, tileY, symbols, scope);
    var gameObject;
    if (scope) {
        gameObject = this.chessCreateCallback.call(scope, board);
    } else {
        gameObject = this.chessCreateCallback(board);
    }
    gameObject.setData('symbol', symbol);
    board.addChess(gameObject, tileX, tileY, this.chessTileZ, true);
    gameObject.rexMoveTo = this.rexBoard.add.moveTo(gameObject, this.chessMoveTo);

    if (this.layer) {
        this.layer.add(gameObject);
    }
}

export default CreateChess;
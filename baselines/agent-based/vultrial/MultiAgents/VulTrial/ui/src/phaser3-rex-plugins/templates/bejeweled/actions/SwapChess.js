var SwapChess = function (chess1, chess2, board, bejeweled) {
    var tileXYZ1 = board.chessToTileXYZ(chess1);
    var tileXYZ2 = board.chessToTileXYZ(chess2);
    var tileX1 = tileXYZ1.x,
        tileY1 = tileXYZ1.y,
        tileX2 = tileXYZ2.x,
        tileY2 = tileXYZ2.y,
        tileZ = tileXYZ1.z;
    board.setChessTileZ(chess2, `#${tileZ}`);
    var moveTo1 = bejeweled.getChessMoveTo(chess1);
    var moveTo2 = bejeweled.getChessMoveTo(chess2);
    moveTo1.moveTo(tileX2, tileY2);
    moveTo2.moveTo(tileX1, tileY1);
    board.setChessTileZ(chess2, tileZ);

    if (moveTo1.isRunning) {
        bejeweled.waitEvent(moveTo1, 'complete');
    }
    if (moveTo2.isRunning) {
        bejeweled.waitEvent(moveTo2, 'complete');
    }
};

export default SwapChess;
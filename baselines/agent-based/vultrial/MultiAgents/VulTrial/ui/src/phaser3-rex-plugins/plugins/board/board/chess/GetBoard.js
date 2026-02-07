var GetBoard = function (chess) {
    if (!chess) {
        return undefined;
    } else if (chess.rexChess) {
        return chess.rexChess.board;
    } else if (chess.mainBoard) {
        return chess.mainBoard;
    } else {
        return undefined;
    }
}

export default GetBoard;
import IsUID from './IsUID.js'

var IsChess = function (chess) {
    if (IsUID(chess)) {
        return false;
    } else {
        return chess && (!!chess.rexChess);
    }
}

export default IsChess;
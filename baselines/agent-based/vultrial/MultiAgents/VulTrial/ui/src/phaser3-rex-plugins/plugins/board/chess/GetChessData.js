import ChessBank from './ChessBank.js';
import ChessData from './ChessData.js';
import IsUID from './IsUID';

var GetChessData = function (gameObject) {
    if (IsUID(gameObject)) {
        return ChessBank.get(gameObject);
    } else {
        if (!gameObject.hasOwnProperty('rexChess')) {
            gameObject.rexChess = new ChessData(gameObject);
        }
        return gameObject.rexChess;
    }
}
export default GetChessData;
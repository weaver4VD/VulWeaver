import IsUID from '../../chess/IsUID.js';
import IsChess from '../../chess/IsChess';
import GetChessUID from '../../chess/GetChessUID.js';
import IsTileXYZ from '../../utils/IsTileXYZ.js';

var ChessToTileXYZ = function (chess) {
    if (!chess) {
        return null;
    }
    if (IsUID(chess) || IsChess(chess)) {
        var uid = GetChessUID(chess);
        return this.boardData.getXYZ(uid);
    } else if (IsTileXYZ(chess)) {
        return chess;
    } else {
        return null;
    }
}
export default ChessToTileXYZ;
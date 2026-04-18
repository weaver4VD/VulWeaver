export default {
    setBoardSize(width, height) {
        this.board.setBoardWidth(width).setBoardHeight(height);
        return this;
    },
    getChessMoveTo(chess) {
        return (chess) ? chess.rexMoveTo : undefined;
    },

    getChessTileZ() {
        return this.board.chessTileZ;
    },

    worldXYToChess(worldX, worldY) {
        return this.board.worldXYToChess(worldX, worldY);
    },

    tileXYToChess(tileX, tileY) {
        return this.board.tileXYToChess(tileX, tileY);
    },

    getNeighborChessAtAngle(chess, angle) {
        return this.board.getNeighborChessAtAngle(chess, angle);
    },

    getNeighborChessAtDirection(chess, direction) {
        return this.board.getNeighborChessAtDirection(chess, direction);
    },
    getBoard() {
        return this.board.board;
    },
    getMatch() {
        return this.board.match;
    }
}
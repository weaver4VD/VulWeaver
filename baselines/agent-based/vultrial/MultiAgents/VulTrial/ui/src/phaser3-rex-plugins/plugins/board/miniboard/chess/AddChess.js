import IsUID from '../../chess/IsUID.js';

var AddChess = function (gameObject, tileX, tileY, tileZ) {
    var grid = this.grid;
    grid.saveOrigin();
    grid.setOriginPosition(this.x, this.y);
    this.board.addChess(gameObject, tileX, tileY, tileZ, true);
    if (IsUID(gameObject)) {
        gameObject = this.board.uidToChess(gameObject);
    }
    this.add(gameObject);

    grid.restoreOrigin();
    return this;
}

export default AddChess;
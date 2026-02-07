import GetValue from '../../../utils/object/GetValue.js';

var MoveToTile = function (tileX, tileY, direction) {
    var miniBoard = this.parent;
    var mainBoard = miniBoard.mainBoard;
    if (mainBoard == null) {
        this.lastMoveResult = false;
        return this;
    }

    if ((tileX != null) && (typeof (tileX) !== 'number')) {
        var config = tileX;
        tileX = GetValue(config, 'x', undefined);
        tileY = GetValue(config, 'y', undefined);
        direction = GetValue(config, 'direction', undefined);
    }
    myTileXY.x = miniBoard.tileX;
    myTileXY.y = miniBoard.tileY;
    if ((direction !== undefined) &&
        (tileX == null) || (tileY == null)) {
        var out = mainBoard.getNeighborTileXY(myTileXY, direction, true);
        if (out !== null) {
            tileX = out.x;
            tileY = out.y;
        } else {
            tileX = null;
            tileY = null;
        }
    }
    if ((tileX == null) || (tileY == null)) {
        this.lastMoveResult = false;
        return this;
    }
    if (direction === undefined) {
        targetTileXY.x = tileX;
        targetTileXY.y = tileY;
        direction = board.getNeighborTileDirection(myTileXY, targetTileXY);
    }
    if (!this.canMoveTo(tileX, tileY, direction)) {
        this.lastMoveResult = false;
        return this;
    }
    this.destinationTileX = tileX;
    this.destinationTileY = tileY;
    this.destinationDirection = direction;
    var out = mainBoard.tileXYToWorldXY(tileX, tileY, true);
    this.moveToTask.moveTo(out.x, out.y);
    miniBoard.putOnMainBoard(mainBoard, tileX, tileY, false);

    this.isRunning = true;
    this.lastMoveResult = true;
    return this;
}

var myTileXY = {};
var targetTileXY = {};

export default MoveToTile;
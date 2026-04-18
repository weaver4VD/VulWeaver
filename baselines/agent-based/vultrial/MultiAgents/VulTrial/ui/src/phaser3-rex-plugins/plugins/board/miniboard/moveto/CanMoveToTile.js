var CanMoveToTile = function (tileX, tileY, direction) {
    var miniBoard = this.parent;
    var mainBoard = miniBoard.mainBoard;
    if (mainBoard == null) {
        return false;
    }

    myTileXYZ.x = miniBoard.tileX;
    myTileXYZ.y = miniBoard.tileY;
    targetTileXYZ.x = tileX;
    targetTileXYZ.y = tileY;
    if ((targetTileXYZ.x === myTileXYZ.x) && (targetTileXYZ.y === myTileXYZ.y)) {
        return true;
    }

    miniBoard.pullOutFromMainBoard();
    if (!miniBoard.canPutOnMainBoard(mainBoard, targetTileXYZ.x, targetTileXYZ.y)) {
        miniBoard.putBack();
        return false;
    }
    if (this.moveableTestCallback) {
        if (direction === undefined) {
            direction = mainBoard.getNeighborTileDirection(myTileXYZ, targetTileXYZ);
        }
        if (this.moveableTestScope) {
            var moveable = this.moveableTestCallback.call(this.moveableTestScope, myTileXYZ, targetTileXYZ, direction, mainBoard);
        } else {
            var moveable = this.moveableTestCallback(myTileXYZ, targetTileXYZ, direction, mainBoard);
        }
        if (!moveable) {
            miniBoard.putBack();
            return false;
        }
    }

    miniBoard.putBack();
    return true;
}

var myTileXYZ = { x: 0, y: 0, z: 0 };
var targetTileXYZ = { x: 0, y: 0, z: 0 };

export default CanMoveToTile;
var MoveAway = function (tileX, tileY, moveAwayMode) {
    var board = this.chessData.board;
    if (board === null) {
        this.lastMoveResult = false;
        return this;
    }

    if (typeof (tileX) !== 'number') {
        var config = tileX;
        tileX = config.x;
        tileY = config.y;
    }
    targetTileXY.x = tileX;
    targetTileXY.y = tileY;
    if (moveAwayMode === undefined) {
        moveAwayMode = true;
    }

    var myTileXYZ = this.chessData.tileXYZ;
    var directions = board.grid.allDirections;
    for (var i = 0, cnt = directions.length + 1; i < cnt; i++) {
        var chessInfo = globChessInfo[i];
        if (!chessInfo) {
            chessInfo = {};
            globChessInfo.push(chessInfo);
        }

        if (i < (cnt - 1)) {
            var out = board.getNeighborTileXY(myTileXYZ, i, chessInfo);
            if (out === null) {
                chessInfo.x = undefined;
                chessInfo.y = undefined;
                chessInfo.distance = undefined;
            } else {
                chessInfo.distance = board.getDistance(chessInfo, targetTileXY, true);
            }
        } else {
            chessInfo.direction = undefined;
            chessInfo.x = myTileXYZ.x;
            chessInfo.y = myTileXYZ.y;
            chessInfo.distance = board.getDistance(chessInfo, targetTileXY, true);
        }

    }
    globChessInfo.length = directions.length + 1;
    var previousDirection = this.destinationDirection;
    globChessInfo.sort(function (infoA, infoB) {
        var distanceA = infoA.distance,
            distanceB = infoB.distance;
        if (distanceA === undefined) {
            return 1;
        }
        if (distanceB === undefined) {
            return -1;
        }

        if (distanceA > distanceB) {
            return (moveAwayMode) ? -1 : 1;
        }
        if (distanceA < distanceB) {
            return (moveAwayMode) ? 1 : -1;
        }
        var directionA = infoA.direction,
            directionB = infoB.direction;
        if (directionA === previousDirection) {
            return 1;
        }
        if (directionB === previousDirection) {
            return -1;
        }
        if (directionA === undefined) {
            return 1;
        }
        if (directionB === undefined) {
            return -1;
        }
        return 0;
    });
    for (var i = 0, cnt = globChessInfo.length; i < cnt; i++) {
        chessInfo = globChessInfo[i];
        if (chessInfo.distance === null) {
            return this;
        }
        this.moveTo(chessInfo);
        if (this.lastMoveResult) {
            return this;
        }
    }
    return this;
}

var targetTileXY = {
    x: 0,
    y: 0
}
var globChessInfo = [];
export default MoveAway;
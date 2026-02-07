var IsInCone = function (targetTileXY) {
    if (this.cone === undefined) {
        return true;
    }
    var board = this.board;
    var myTileXYZ = this.chessData.tileXYZ;
    if (this.coneMode === 0) {
        return board.isDirectionInCone(myTileXYZ, targetTileXY, this.face, this.cone);
    } else {
        return board.isAngleInCone(myTileXYZ, targetTileXY, this.faceAngle, this.coneRad);
    }
}
export default IsInCone;
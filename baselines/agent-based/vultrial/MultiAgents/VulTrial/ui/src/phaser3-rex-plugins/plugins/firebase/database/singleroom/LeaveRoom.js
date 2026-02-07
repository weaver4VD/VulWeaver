var LeaveRoom = function () {
    if (!this.isInRoom()) {
        return Promise.resolve();
    }
    this.leftRoomFlag = true;
    return this.userList.leave();
}

export default LeaveRoom;
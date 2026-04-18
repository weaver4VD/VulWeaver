var LeaveRoom = function () {
    if (!this.isInRoom()) {
        return Promise.resolve();
    }
    this.leftRoomFlag = true;
    if (this.isRemoveRoomWhenLeft) {
        return this.removeRoom()
    } else {
        var prevRoomInfo = this.getRoomInfo();
        return this.userList.leave()
            .then(function () {
                return Promise.resolve(prevRoomInfo)
            })
    }
}

export default LeaveRoom;
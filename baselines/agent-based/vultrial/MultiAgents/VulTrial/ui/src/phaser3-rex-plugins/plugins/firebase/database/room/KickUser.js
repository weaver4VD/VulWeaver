var KickUser = function (userID) {
    if (!this.userList.contains(userID)) {
        return Promise.resolve();
    } else if (userID === this.userID) {
        return this.leaveRoom();
    } else {
        return this.userList.leave(userID);
    }
}

export default KickUser;
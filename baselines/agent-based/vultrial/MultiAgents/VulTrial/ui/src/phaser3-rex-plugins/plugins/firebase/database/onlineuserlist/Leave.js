var Leave = function (userID) {
    if (userID === undefined) {
        userID = this.userID;
    }

    if (!this.contains(userID)) {
        return Promise.resolve();
    }
    var itemID = this.userID2ItemID[userID];
    var userRef = this.database.ref(this.rootPath).child(itemID);
    return userRef.remove();
}

export default Leave;
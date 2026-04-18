import OnlineUserList from '../../onlineuserlist/OnlineUserList.js';

var CreateUserList = function (config) {
    var userList = new OnlineUserList({
        eventEmitter: this.getEventEmitter(),
        eventNames: {
            join: 'userlist.join',
            leave: 'userlist.leave',
            update: 'userlist.update',
            change: 'userlist.change',
            init: 'userlist.init',
            changename: 'userlist.changename'
        },

        userID: this.userInfo
    });
    userList
        .on('userlist.leave', function (user) {
            if (user.userID === this.userID) {
                OnLeftRoom.call(this);
            }
        }, this)

    this
        .on('room.join', function () {
            userList
                .startUpdate()
        })
        .on('room.leave', function () {
            userList
                .stopUpdate()
                .clear()
        })

    return userList;
}

var OnLeftRoom = function () {
    this.emit('room.leave');
    var self = this;
    setTimeout(function () {
        self.roomID = undefined;
        self.roomName = undefined;
        self.doorState = undefined;
        self.leftRoomFlag = false;
    }, 0);
}

export default CreateUserList;
import EventEmitterMethods from '../../../utils/eventemitter/EventEmitterMethods.js';
import GetValue from '../../../utils/object/GetValue.js';
import CreateUserList from './utils/CreateUserList.js';
import CreateRoomList from './utils/CreateRoomList.js';
import CreateBroadcast from './utils/CreateBroadcast.js';
import CreateTables from './utils/CreateTables.js';
import IsPlainObject from '../../../utils/object/IsPlainObject.js';
import Methods from './Methods.js';

class Room {
    constructor(config) {
        var eventEmitter = GetValue(config, 'eventEmitter', undefined);
        var EventEmitterClass = GetValue(config, 'EventEmitterClass', undefined);
        this.setEventEmitter(eventEmitter, EventEmitterClass);

        this.database = firebase.database()
        this.rootPath = GetValue(config, 'root', '');
        this.userInfo = { userID: '', userName: '' };
        this.setUser(GetValue(config, 'userID', ''), GetValue(config, 'userName', ''));
        this.isRoomCreator = false;
        this.roomID = undefined;
        this.roomName = undefined;
        this.roomType = undefined;
        this.doorState = undefined;
        this.leftRoomFlag = false;
        this.isRemoveRoomWhenLeft = undefined;
        this.userList = CreateUserList.call(this, config);
        this.roomList = CreateRoomList.call(this, config);
        this.broadcast = CreateBroadcast.call(this, config);
        this.tables = CreateTables.call(this, config);
    }

    shutdown() {
        var self = this;
        this
            .destroyEventEmitter()
            .leaveRoom()
            .then(function () {
                self.userList.destroy();
                self.userList = undefined;

                self.roomList.destroy();
                self.roomList = undefined;

                self.broadcast.destroy();
                self.broadcast = undefined;
            })
    }

    destroy() {
        this.shutdown();
    }

    get userID() {
        return this.userInfo.userID;
    }

    set userID(value) {
        this.userInfo.userID = value;
    }

    get userName() {
        return this.userInfo.userName;
    }

    set userName(value) {
        this.userInfo.userName = value;
    }

    getRoomInfo(roomID, roomName) {
        if (roomID === undefined) {
            roomID = this.roomID;
        }
        if (roomName === undefined) {
            roomName = this.roomName;
        }
        return { roomID: roomID, roomName: roomName };
    }

    setUser(userID, userName) {
        if (IsPlainObject(userID)) {
            this.userInfo = userID;
        } else {
            this.userID = userID;
            this.userName = userName;
        }
        return this;
    }

    isInRoom(roomID) {
        return (roomID === undefined) ? (this.roomID !== undefined) : (this.roomID === roomID);
    }

    isFull() {
        return this.userList.isFull();
    }

    isFirstUser(userID) {
        return this.userList.isFirstUser(userID);
    }

    getUsers() {
        return this.userList.getUsers();
    }

    get maxUsers() {
        return this.userList.maxUsers;
    }

    getTable(key) {
        return this.tables[key];
    }
}


Object.assign(
    Room.prototype,
    EventEmitterMethods,
    Methods
);

export default Room;
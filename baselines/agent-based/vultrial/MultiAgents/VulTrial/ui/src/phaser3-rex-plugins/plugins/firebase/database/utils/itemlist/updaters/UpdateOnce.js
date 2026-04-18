import { GetAllChildrenCallback } from './Callbacks.js';

var Updater = {
    start(query) {
        this.isUpdating = false;
        query.once('value', GetAllChildrenCallback, this);
        return this;
    },
    stop() {
        return this;
    }
}

export default Updater;
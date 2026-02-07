import NOOP from '../../../utils/object/NOOP.js';

export default {
    setTransitInTime(time) {
        this.transitInTime = time;
        return this;
    },

    setTransitOutTime(time) {
        this.transitOutTime = time;
        return this;
    },

    setTransitInCallback(callback) {
        if (!callback) {
            callback = NOOP;
        }

        this.transitInCallback = callback;
        return this;
    },

    setTransitOutCallback(callback) {
        if (!callback) {
            callback = NOOP;
        }

        this.transitOutCallback = callback;
        return this;
    },

}
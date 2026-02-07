import PostUpdateDelayCall from '../../../../plugins/utils/time/PostUpdateDelayCall.js';

export default {
    delayCall(delay, callback, scope) {
        this.timer = PostUpdateDelayCall(this, delay, callback, scope);
        return this;
    },

    removeDelayCall() {
        if (this.timer) {
            this.timer.remove(false);
            this.timer = undefined;
        }
        return this;
    }
}
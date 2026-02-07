import PostStepDelayCall from '../../../utils/time/PostStepDelayCall.js';

export default {
    delayCall(delay, callback, scope) {
        this.delayCallTimer = PostStepDelayCall(this, delay, callback, scope);
        return this;
    },

    removeDelayCall() {
        if (this.delayCallTimer) {
            this.delayCallTimer.remove(false);
            this.delayCallTimer = undefined;
        }
        return this;
    }

}
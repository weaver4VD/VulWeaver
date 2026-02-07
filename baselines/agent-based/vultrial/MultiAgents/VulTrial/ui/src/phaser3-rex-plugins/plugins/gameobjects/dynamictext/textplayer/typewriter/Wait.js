import WaitMultiple from '../methods/utils/wait/WaitMultiple.js';

var Wait = function (name) {
    if (this.ignoreWait) {
        return this;
    }

    this.pauseTyping();
    WaitMultiple(this.textPlayer, name, this.resumeTyping, [], this);

    return this;
}

export default Wait;
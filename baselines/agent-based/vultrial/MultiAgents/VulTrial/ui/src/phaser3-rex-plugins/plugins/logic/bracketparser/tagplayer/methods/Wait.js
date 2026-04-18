import WaitMultiple from './utils/wait/WaitMultiple.js';

var Wait = function (name) {
    if (this.ignoreWait) {
        return this;
    }

    this.pause();
    WaitMultiple(this, name, this.resume, [], this);

    return this;
}

export default Wait;
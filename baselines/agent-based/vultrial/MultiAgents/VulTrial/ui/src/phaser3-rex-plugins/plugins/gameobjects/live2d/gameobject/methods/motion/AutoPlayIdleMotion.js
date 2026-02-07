import * as Const from '../../model/Const.js';

var AutoPlayIdleMotion = function (motionName) {
    if (!this.autoPlayIdleMotionCallback && !motionName) {
        return this;
    }
    if (!this.autoPlayIdleMotionCallback) {
        this.autoPlayIdleMotionCallback = function () {
            if (!this.idleMotionName) {
                return;
            }
            this.startMotion(this.idleMotionName, undefined, Const.PriorityIdle);
        }
        this.on('idle', this.autoPlayIdleMotionCallback, this);
    }
    this.idleMotionName = motionName;

    return this;
}

export default AutoPlayIdleMotion;
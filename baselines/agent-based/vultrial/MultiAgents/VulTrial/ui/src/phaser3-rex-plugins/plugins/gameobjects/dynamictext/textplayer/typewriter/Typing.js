import { IsCommand, IsSpaceChar } from '../../dynamictext/bob/Types.js';
import { TypingDelayTimerType, TypingAnimationTimerType, } from './TimerTypes.js';

var Typing = function (offsetTime) {
    if (offsetTime === undefined) {
        offsetTime = 0;
    }

    var delay = 0;
    this.inTypingProcessLoop = true;
    while (this.inTypingProcessLoop) {
        var child = this.getNextChild();
        if (!child) {
            if (this.timeline.isRunning) {
                this.timeline.once('complete', function () {
                    this.isPageTyping = false;
                    this.emit('complete');
                }, this);
            } else {
                this.isPageTyping = false;
                this.emit('complete');
            }
            break;
        }

        if (child.renderable) {
            var animationConfig = this.animationConfig;
            if (animationConfig.duration > 0) {
                var animationTimer = this.timeline.addTimer({
                    name: TypingAnimationTimerType,
                    target: child,
                    duration: animationConfig.duration,
                    yoyo: animationConfig.yoyo,
                    onStart: animationConfig.onStart,
                    onProgress: animationConfig.onProgress,
                    onComplete: animationConfig.onComplete,
                })
                if (this.skipTypingAnimation) {
                    animationTimer.seek(1);
                }
            } else {
                if (animationConfig.onStart) {
                    animationConfig.onStart(child, 0);
                }
            }
            if (this.minSizeEnable) {
                this.textPlayer.setToMinSize();
            }

            this.textPlayer.emit('typing', child);

            var nextChild = this.nextChild;
            if (nextChild) {
                if (this.skipSpaceEnable && IsSpaceChar(nextChild)) {
                } else {
                    delay += (this.speed + offsetTime);
                    offsetTime = 0;
                    if (delay > 0) {
                        this.typingTimer = this.timeline.addTimer({
                            name: TypingDelayTimerType,
                            target: this,
                            duration: delay,
                            onComplete: function (target, t, timer) {
                                target.typingTimer = undefined;
                                Typing.call(target, timer.remainder);
                            }
                        })
                        break;
                    }
                }
            }
        } else if (IsCommand(child)) {
            child.exec();
        }

    }
    if (this.minSizeEnable) {
        this.textPlayer.setToMinSize();
    }

    this.inTypingProcessLoop = false;
}

export default Typing;
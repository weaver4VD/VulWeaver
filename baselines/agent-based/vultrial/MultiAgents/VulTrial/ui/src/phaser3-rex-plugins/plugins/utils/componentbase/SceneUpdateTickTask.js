import TickTask from './TickTask.js';

const GetValue = Phaser.Utils.Objects.GetValue;

class SceneUpdateTickTask extends TickTask {
    constructor(parent, config) {
        super(parent, config);
        var defaultEventName = (this.scene) ? 'update' : 'step';
        this.tickEventName = GetValue(config, 'tickEventName', defaultEventName);
        this.isSceneTicker = !IsGameUpdateEvent(this.tickEventName);

    }

    startTicking() {
        super.startTicking();

        if (this.isSceneTicker) {
            this.scene.sys.events.on(this.tickEventName, this.update, this);
        } else {
            this.game.events.on(this.tickEventName, this.update, this);
        }

    }

    stopTicking() {
        super.stopTicking();

        if (this.isSceneTicker && this.scene) {
            this.scene.sys.events.off(this.tickEventName, this.update, this);
        } else if (this.game) {
            this.game.events.off(this.tickEventName, this.update, this);
        }
    }

}

var IsGameUpdateEvent = function (eventName) {
    return (eventName === 'step') || (eventName === 'poststep');
}

export default SceneUpdateTickTask;
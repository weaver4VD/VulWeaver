import ComponentBase from './ComponentBase.js';

const GetValue = Phaser.Utils.Objects.GetValue;

class TickTask extends ComponentBase {
    constructor(parent, config) {
        super(parent, config);

        this._isRunning = false;
        this.isPaused = false;
        this.tickingState = false;
        this.setTickingMode(GetValue(config, 'tickingMode', 1));
    }
    boot() {
        if ((this.tickingMode === 2) && (!this.tickingState)) {
            this.startTicking();
        }
    }
    shutdown(fromScene) {
        if (this.isShutdown) {
            return;
        }

        this.stop();
        if (this.tickingState) {
            this.stopTicking();
        }
        super.shutdown(fromScene);
    }

    setTickingMode(mode) {
        if (typeof (mode) === 'string') {
            mode = TICKINGMODE[mode];
        }
        this.tickingMode = mode;
    }
    startTicking() {
        this.tickingState = true;
    }
    stopTicking() {
        this.tickingState = false;
    }

    get isRunning() {
        return this._isRunning;
    }

    set isRunning(value) {
        if (this._isRunning === value) {
            return;
        }

        this._isRunning = value;
        if ((this.tickingMode === 1) && (value != this.tickingState)) {
            if (value) {
                this.startTicking();
            } else {
                this.stopTicking();
            }
        }
    }

    start() {
        this.isPaused = false;
        this.isRunning = true;
        return this;
    }

    pause() {
        if (this.isRunning) {
            this.isPaused = true;
            this.isRunning = false;
        }
        return this;
    }

    resume() {
        if (this.isPaused) {
            this.isRunning = true;
        }
        return this;
    }

    stop() {
        this.isPaused = false;
        this.isRunning = false;
        return this;
    }

    complete() {
        this.isPaused = false;
        this.isRunning = false;
        this.emit('complete', this.parent, this);
    }
}

const TICKINGMODE = {
    'no': 0,
    'lazy': 1,
    'always': 2
}

export default TickTask;
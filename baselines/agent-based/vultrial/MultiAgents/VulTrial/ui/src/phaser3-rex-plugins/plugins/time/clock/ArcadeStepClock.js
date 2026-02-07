import BaseClock from './BaseClock.js';

class ArcadeStepClock extends BaseClock {
    startTicking() {
        super.startTicking();
        this.scene.physics.world.on('worldstep', this.update, this);
    }

    stopTicking() {
        super.stopTicking();
        if (this.scene) {
            this.scene.physics.world.off('worldstep', this.update, this);
        }
    }

    update() {
        if ((!this.isRunning) || (this.timeScale === 0)) {
            return this;
        }
        this.tick(1);
        return this;
    }
}

export default ArcadeStepClock;
import BasePlayer from '../tcrp/Player.js';
import ArcadeStepClock from '../../../time/clock/ArcadeStepClock';

class Player extends BasePlayer {
    constructor(parent, config) {
        if (config === undefined) {
            config = {};
        }
        config.clock = new ArcadeStepClock(parent);
        config.timeUnit = 0;
        config.dtMode = 0;
        super(parent, config);
    }

    load(commands, scope, config) {
        super.load(commands, scope);
        return this;
    }
}

export default Player;
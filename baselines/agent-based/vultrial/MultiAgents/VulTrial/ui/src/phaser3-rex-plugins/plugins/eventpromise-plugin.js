import { WaitEvent, WaitComplete, Delay } from './eventpromise.js'

class EventPromisePlugin extends Phaser.Plugins.BasePlugin {

    constructor(pluginManager) {
        super(pluginManager);
    }
}

var methods = {
    waitEvent: WaitEvent,
    waitComplete: WaitComplete,
    delay: Delay,
}
Object.assign(
    EventPromisePlugin.prototype,
    methods
);

export default EventPromisePlugin;
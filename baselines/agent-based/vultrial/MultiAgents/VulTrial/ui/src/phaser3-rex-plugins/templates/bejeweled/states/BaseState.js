import FSM from '../../../plugins/fsm.js';

class BaseState extends FSM {
    constructor(bejeweled, config) {
        super(config);

        this.bejeweled = bejeweled;
        this.board = bejeweled.board;
        this.waitEvents = bejeweled.waitEvents;
    }

    shutdown() {
        super.shutdown();
        this.bejeweled = undefined;
        this.board = undefined;
        this.waitEvents = undefined;
    }

    destroy() {
        this.shutdown();
        return this;
    }

    next() {
        if (this.waitEvents.noWaitEvent) {
            super.next();  
        } else {
            this.waitEvents.setCompleteCallback(this.next, this);
        }
    }
}

export default BaseState
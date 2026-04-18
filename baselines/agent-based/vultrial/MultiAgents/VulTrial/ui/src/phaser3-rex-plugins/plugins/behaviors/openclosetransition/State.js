import FSM from '../../fsm.js';



class State extends FSM {
    constructor(parent, config) {
        super(config);
        this.parent = parent;

        var initState = config.initState || 'IDLE';
        this.start(initState);
    }

    init() {
        this.start('IDLE');
    }
    next_IDLE() {
        return 'TRANS_OPNE';
    }
    next_TRANS_OPNE() {
        return 'OPEN';
    }
    enter_TRANS_OPNE() {
        var transitionBehavior = this.parent;
        if (transitionBehavior.transitInTime > 0) {
            var delay = transitionBehavior.runTransitionInCallback();
            transitionBehavior.delayCall(delay, this.next, this);
        } else {
            this.next();
        }
    }
    exit_TRANS_OPNE() {
        var transitionBehavior = this.parent;
        transitionBehavior.removeDelayCall();
    }
    next_OPEN() {
        return 'TRANS_CLOSE';
    }
    enter_OPEN() {
        var transitionBehavior = this.parent;
        transitionBehavior.onOpen();
    }
    exit_OPEN() {
        var transitionBehavior = this.parent;
        transitionBehavior.removeDelayCall();
    }
    next_TRANS_CLOSE() {
        return 'CLOSE';
    }
    enter_TRANS_CLOSE() {
        var transitionBehavior = this.parent;
        if (transitionBehavior.transitOutTime > 0) {
            var delay = transitionBehavior.runTransitionOutCallback();
            transitionBehavior.delayCall(delay, this.next, this);
        } else {
            this.next();
        }
    }
    exit_TRANS_CLOSE() {
        var transitionBehavior = this.parent;
        transitionBehavior.removeDelayCall();
    }
    next_CLOSE() {
        return 'TRANS_OPNE';
    }
    enter_CLOSE() {
        var transitionBehavior = this.parent;
        transitionBehavior.onClose();
    }
    exit_CLOSE() {
    }

    canOpen() {
        return (this.state === 'IDLE') || (this.state === 'CLOSE');
    }

    canClose() {
        return (this.state === 'IDLE') || (this.state === 'OPEN');
    }
}

export default State;
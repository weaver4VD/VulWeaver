import BaseState from './BaseState.js';
import MatchState from './MatchState.js';
import SelectChess from '../actions/SelectChess.js';
import SwapChess from '../actions/SwapChess.js'

const GetValue = Phaser.Utils.Objects.GetValue;

class State extends BaseState {
    constructor(bejeweled, config) {
        super(bejeweled, config);

        this.selectedChess1;
        this.selectedChess2;
        this.matchState = new MatchState(bejeweled, config);
        this.select1Action = GetValue(config, 'select1Action', SelectChess);
        this.select2Action = GetValue(config, 'select2Action', this.select1Action);
        this.swapAction = GetValue(config, 'swapAction', SwapChess);
        this.undoSwapAction = GetValue(config, 'undoSwapAction', this.swapAction);

        var debug = GetValue(config, 'debug', false);
        if (debug) {
            this.on('statechange', this.printState, this);
        }
    }

    shutdown() {
        super.shutdown();

        this.matchState.shutdown();

        this.matchState = undefined;
        this.selectedChess1 = undefined;
        this.selectedChess2 = undefined;
        return this;
    }
    enter_START() {
        this.board.init();
        this.next();
    }
    next_START() {
        return 'RESET';
    }
    enter_RESET() {
        this.board.reset();
        this.next();
    }
    next_RESET() {
        return 'PRETEST';
    }
    enter_PRETEST() {
        this.next();
    }
    next_PRETEST() {
        var nextState;
        if (this.board.preTest()) {
            nextState = 'SELECT1START';
        } else {
            nextState = 'RESET';
        }
        return nextState;
    }
    enter_SELECT1() {
        this.selectedChess1 = undefined;
        this.selectedChess2 = undefined;

        this.bejeweled.emit('select1-start', this.board.board, this.bejeweled);
    }
    selectChess1(chess) {
        if (this.state === 'SELECT1START') {
            this.selectedChess1 = chess;
            this.next();
        }
        return this;
    }
    next_SELECT1START() {
        var nextState;
        if (this.selectedChess1) {
            nextState = 'SELECT1';
        }
        return nextState;
    }
    enter_SELECT1() {
        var board = this.board.board,
            chess = this.selectedChess1;

        this.bejeweled.emit('select1', chess, board, this.bejeweled);

        this.select1Action(chess, board, this.bejeweled);
        this.next();
    }
    next_SELECT1() {
        return 'SELECT2START';
    }
    enter_SELECT2START() {
        this.bejeweled.emit('select2-start', this.board.board, this.bejeweled);
    }
    selectChess2(chess) {
        if (this.state === 'SELECT2START') {
            this.selectedChess2 = chess;
            this.next();
        }
        return this;
    }
    next_SELECT2START() {
        var nextState;
        if (this.selectedChess2 &&
            this.board.board.areNeighbors(this.selectedChess1, this.selectedChess2)) {
            nextState = 'SELECT2';
        } else {
            nextState = 'SELECT1START';
        }
        return nextState;
    }
    enter_SELECT2() {
        var board = this.board.board,
            chess = this.selectedChess2;

        this.bejeweled.emit('select2', chess, board, this.bejeweled);

        this.select2Action(chess, board, this.bejeweled);
        this.next();
    }
    next_SELECT2() {
        return 'SWAP';
    }
    enter_SWAP() {
        var board = this.board.board,
            chess1 = this.selectedChess1,
            chess2 = this.selectedChess2;

        this.bejeweled.emit('swap', chess1, chess2, board, this.bejeweled);

        this.swapAction(chess1, chess2, board, this.bejeweled);
        this.next();
    }
    next_SWAP() {
        return 'MATCH3';
    }
    enter_MATCH3() {
        this.matchState
            .once('complete', this.next, this)
            .goto('START');
    }
    next_MATCH3() {
        var nextState;
        if (this.matchState.totalMatchedLinesCount === 0) {
            nextState = 'UNDOSWAP';
        } else {
            nextState = 'PRETEST';
        }
        return nextState;
    }
    enter_UNDOSWAP() {
        var board = this.board.board,
            chess1 = this.selectedChess1,
            chess2 = this.selectedChess2;

        this.bejeweled.emit('undo-swap', chess1, chess2, board, this.bejeweled);

        this.undoSwapAction(chess1, chess2, board, this.bejeweled);
        this.next();
    }
    next_UNDOSWAP() {
        return 'SELECT1START';
    }
    printState() {
        console.log('Main state: ' + this.prevState + ' -> ' + this.state);
    }

}

export default State;
import BaseState from './BaseState.js';
import EliminateChess from '../actions/EliminateChess.js';
import FallingAllChess from '../actions/FallingAllChess.js';

const GetValue = Phaser.Utils.Objects.GetValue;
const SetStruct = Phaser.Structs.Set;

class State extends BaseState {
    constructor(bejeweled, config) {
        super(bejeweled, config);

        this.totalMatchedLinesCount = 0;
        this.eliminatedChessArray;
        this.eliminatingAction = GetValue(config, 'eliminatingAction', EliminateChess);
        this.fallingAction = GetValue(config, 'fallingAction', FallingAllChess);

        var debug = GetValue(config, 'debug', false);
        if (debug) {
            this.on('statechange', this.printState, this);
        }
    }

    shutdown() {
        super.shutdown();

        this.eliminatedChessArray = undefined;
        this.eliminatingAction = undefined;
        this.fallingAction = undefined;
        return this;
    }

    destroy() {
        this.shutdown();
        return this;
    }
    enter_START() {
        this.totalMatchedLinesCount = 0;

        this.bejeweled.emit('match-start', this.board.board, this.bejeweled);

        this.next();
    }
    next_START() {
        return 'MATCH3';
    }
    enter_MATCH3() {
        var matchedLines = this.board.getAllMatch();

        this.bejeweled.emit('match', matchedLines, this.board.board, this.bejeweled);

        var matchedLinesCount = matchedLines.length;
        this.totalMatchedLinesCount += matchedLinesCount;
        switch (matchedLinesCount) {
            case 0:
                this.eliminatedChessArray = [];
                break;
            case 1:
                this.eliminatedChessArray = matchedLines[0].entries;
                break;
            default:
                var newSet = new SetStruct();
                for (var i = 0; i < matchedLinesCount; i++) {
                    matchedLines[i].entries.forEach(function (value) {
                        newSet.set(value);
                    });
                }
                this.eliminatedChessArray = newSet.entries;
                break;
        }
        this.next();
    }
    next_MATCH3() {
        var nextState;
        if (this.eliminatedChessArray.length === 0) {
            nextState = 'END'
        } else {
            nextState = 'ELIMINATING';
        }
        return nextState;
    }
    enter_ELIMINATING() {
        var board = this.board.board,
            chessArray = this.eliminatedChessArray;

        this.bejeweled.emit('eliminate', chessArray, board, this.bejeweled);

        this.eliminatingAction(chessArray, board, this.bejeweled);
        chessArray.forEach(board.removeChess, board);
        this.next();
    }
    next_ELIMINATING() {
        return 'FALLING';
    }
    exit_ELIMINATING() {
        this.eliminatedChessArray = undefined;
    }
    enter_FALLING() {
        var board = this.board.board;

        this.bejeweled.emit('fall', board, this.bejeweled);

        this.fallingAction(board, this.bejeweled);
        this.next();
    }
    next_FALLING() {
        return 'FILL';
    }
    enter_FILL() {
        this.board.fill(true);

        this.bejeweled.emit('fill', this.board.board, this.bejeweled);

        this.next();
    }
    next_FILL() {
        return 'MATCH3';
    }
    enter_END() {
        this.bejeweled.emit('match-end', this.board.board, this.bejeweled);

        this.emit('complete');
    }

    printState() {
        console.log('Match state: ' + this.prevState + ' -> ' + this.state);
    }
}
export default State;


var Reset = function() {
    this.board.removeAllChess();
    this.fill(this.initSymbolsMap);
    this.breakMatch3();
}

export default Reset;
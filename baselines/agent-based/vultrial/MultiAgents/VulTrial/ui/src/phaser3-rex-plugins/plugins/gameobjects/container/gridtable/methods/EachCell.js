var EachVisibleCell = function (callback, scope) {
    this.visibleCells.each(callback, scope);
    return this;
}
var IterateVisibleCell = function (callback, scope) {
    this.visibleCells.iterate(callback, scope);
    return this;
}

var EachCell = function (callback, scope) {
    this.table.cells.slice().forEach(callback, scope);
    return this;
}

var IterateCell = function (callback, scope) {
    this.table.cells.forEach(callback, scope);
    return this;
}

export { EachVisibleCell, IterateVisibleCell, EachCell, IterateCell };
var HideCell = function (cell) {
    this.emit('cellinvisible', cell);

    if (this.cellContainersPool) {
        var cellContainer = cell.popContainer();
        if (cellContainer) {
            this.cellContainersPool.killAndHide(cellContainer);
        }
    }

    cell.destroyContainer();
}

export default HideCell;
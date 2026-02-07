var ShowCell = function (cell) {
    var reusedCellContainer = null;
    var cellContainer = cell.getContainer();
    if (cellContainer) {
        reusedCellContainer = cellContainer;
        cell.popContainer();
    } else if (this.cellContainersPool) {
        reusedCellContainer = this.cellContainersPool.getFirstDead();
        if (reusedCellContainer !== null) {
            reusedCellContainer.setActive(true).setVisible(true);
        }
    }

    this.emit('cellvisible', cell, reusedCellContainer, this);

    if (this.cellContainersPool) {
        var cellContainer = cell.getContainer();
        if (cellContainer) {
            if (reusedCellContainer === null) {
                this.cellContainersPool.add(cellContainer);
            } else if (reusedCellContainer !== cellContainer) {
                this.cellContainersPool.add(cellContainer);
                this.cellContainersPool.killAndHide(reusedCellContainer);
            }
        } else {
            if (reusedCellContainer !== null) {
                this.cellContainersPool.killAndHide(reusedCellContainer);
            }
        }
    }
}

export default ShowCell;
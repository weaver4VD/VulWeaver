import Board from '../board/Board.js';

var CreateBoard = function (tilemap) {
    var board = new Board(tilemap.scene, {
        grid: CreateGridConfig(tilemap),
        width: tilemap.width,
        height: tilemap.height
    })

    return board;
}

var CreateGridConfig = function (tilemap) {
    var grid = {
        cellWidth: tilemap.tileWidth,
        cellHeight: tilemap.tileHeight,
    }

    switch (tilemap.orientation) {
        case 0:
            grid.gridType = 'quadGrid';
            grid.type = 'orthogonal';
            break;

        case 1:
            grid.gridType = 'quadGrid';
            grid.type = 'isometric';
            break;

        case 3:
            grid.gridType = 'hexagonGrid';
            grid.staggeraxis = 'y';
            grid.staggerindex = 'odd';
            break;

        default:
            grid.gridType = 'quadGrid';
            grid.type = 'orthogonal';
            break;
    }

    var layer = tilemap.layers[0];
    if (layer) {
        grid.x = layer.x;
        grid.y = layer.y;
    }

    return grid;
}

export default CreateBoard;
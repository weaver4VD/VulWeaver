import QuadGrid from '../utils/grid/quad/Quad.js';
import GlobZone from '../utils/actions/GlobZone.js';
import AlignIn from '../utils/align/align/in/QuickSet.js';

const GetFastValue = Phaser.Utils.Objects.GetFastValue;

var globQuadGrid = new QuadGrid();



var GridAlign = function (items, options) {
    if (options === undefined) {
        options = {};
    }

    var width = GetFastValue(options, 'width', -1);
    var height = GetFastValue(options, 'height', -1);
    var cellWidth = GetFastValue(options, 'cellWidth', 1);
    var cellHeight = GetFastValue(options, 'cellHeight', cellWidth);
    var type = GetFastValue(options, 'type', 0);
    var position = GetFastValue(options, 'position', Phaser.Display.Align.CENTER);
    var x = GetFastValue(options, 'x', 0);
    var y = GetFastValue(options, 'y', 0);

    globQuadGrid
        .setOriginPosition(x, y)
        .setCellSize(cellWidth, cellHeight)
        .setType(type);

    GlobZone.setSize(cellWidth, cellHeight);

    var lastRowIdx = height - 1,
        lastColIdx = width - 1,
        rowIdx = 0,
        colIdx = 0;

    for (var i = 0, cnt = items.length; i < cnt; i++) {
        globQuadGrid.getWorldXY(colIdx, rowIdx, GlobZone);
        AlignIn(items[i], GlobZone, position);

        if (width === -1) {
            rowIdx++;
        } else if (height === -1) {
            colIdx++;
        } else {
            if (colIdx === lastColIdx) {
                if (rowIdx === lastRowIdx) {
                    break;
                } else {
                    colIdx = 0;
                    rowIdx++;
                }
            } else {
                colIdx++;
            }
        }
    }

    return items;
};


export default GridAlign;
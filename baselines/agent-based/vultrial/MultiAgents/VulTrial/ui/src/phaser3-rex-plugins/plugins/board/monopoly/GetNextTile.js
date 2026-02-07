import { CreateTileData } from './TileData.js';
import AreTileXYEqual from '../utils/AreTileXYEqual.js';

import GetRandom from '../../utils/array/GetRandom.js';

var GetNextTile = function (curTileData, preTileData) {
    var board = this.board;
    var directions = board.grid.allDirections;
    var forwardTileData = null,
        backwardTileData = null;
    var neighborTileXArray = [];
    var neighborTileXY, neighborTileData = null;
    for (var i = 0, cnt = directions.length; i < cnt; i++) {
        neighborTileXY = board.getNeighborTileXY(curTileData, directions[i], true);
        if (neighborTileXY === null) {
            continue;
        }
        if (!board.contains(neighborTileXY.x, neighborTileXY.y, this.pathTileZ)) {
            continue;
        }
        neighborTileData = CreateTileData(neighborTileXY.x, neighborTileXY.y, directions[i]);

        if (directions[i] === curTileData.direction) {
            forwardTileData = neighborTileData;
        }
        if ((preTileData !== undefined) && (AreTileXYEqual(neighborTileXY, preTileData))) {
            backwardTileData = neighborTileData;
        } else {
            neighborTileXArray.push(neighborTileData);
        }
    }

    var nextTileData;
    if ((backwardTileData === null) && (neighborTileXArray.length === 0)) {
        nextTileData = null;
    } else if ((backwardTileData === null) && (neighborTileXArray.length === 1)) {
        nextTileData = neighborTileXArray[0];
    } else if ((backwardTileData !== null) && (neighborTileXArray.length === 0)) {
        nextTileData = backwardTileData;
    } else {
        switch (this.pickMode) {
            case 1:
                if (backwardTileData !== null) {
                    neighborTileXArray.push(backwardTileData);
                }
                nextTileData = GetRandom(neighborTileXArray);
                break;

            default:
                if (forwardTileData !== null) {
                    nextTileData = forwardTileData;
                } else {
                    nextTileData = GetRandom(neighborTileXArray);
                }
                break;
        }
    }

    return nextTileData;
}

export default GetNextTile;
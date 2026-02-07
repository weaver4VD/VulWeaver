

import NodeManager from './NodeManager.js';
import BinaryHeap from './BinaryHeap.js';
import CONST from '../const.js';

const AREA_MODE = CONST.AREA_MODE;
const PATH_MODE = CONST.PATH_MODE;

const ASTAR = CONST['A*'];
const ASTAR_LINE = CONST['A*-line'];
const ASTAR_RANDOM = CONST['A*-random'];

const BLOCKER = CONST.BLOCKER;
const INFINITY = CONST.INFINITY;
var gOpenHeap = new BinaryHeap(function (node) {
    return node.f;
});

var AStarSerach = function (startTileXYZ, endTileXY, movingPoints, mode) {
    if (this.nodeManager === undefined) {
        this.nodeManager = new NodeManager(this);
    }
    var nodeManager = this.nodeManager;
    nodeManager.freeAllNodes();
    const isPathSearch = (mode === PATH_MODE);
    const isAStarMode = (this.pathMode === ASTAR) || (this.pathMode === ASTAR_LINE) || (this.pathMode === ASTAR_RANDOM);
    const astarHeuristicEnable = isPathSearch && isAStarMode;
    const shortestPathEnable = isPathSearch && (!isAStarMode);
    const astarHeuristicMode =
        (!astarHeuristicEnable) ? null :
            (this.pathMode == ASTAR) ? 0 :
                (this.pathMode == ASTAR_LINE) ? 1 :
                    (this.pathMode == ASTAR_RANDOM) ? 2 :
                        null;

    var end = (endTileXY !== null) ? nodeManager.getNode(endTileXY.x, endTileXY.y, true) : null;
    var start = nodeManager.getNode(startTileXYZ.x, startTileXYZ.y, true);
    start.h = start.heuristic(end, astarHeuristicMode);
    var closestNode;
    if (isPathSearch) {
        closestNode = start;
        closestNode.closerH = closestNode.h || closestNode.heuristic(end, 0);
    }

    gOpenHeap.push(start);
    while (gOpenHeap.size() > 0) {
        var curNode = gOpenHeap.pop();
        if (isPathSearch && (curNode === end)) {
            closestNode = end;
            break;
        }
        curNode.closed = true;
        var neighbors = curNode.getNeighborNodes();

        var neighbor, neighborCost, isNeighborMoreCloser;
        for (var i = 0, cnt = neighbors.length; i < cnt; ++i) {
            neighbor = neighbors[i];
            neighborCost = neighbor.getCost(curNode);
            if (neighbor.closed || (neighborCost === BLOCKER)) {
                continue;
            }
            var gScore = curNode.g + neighborCost,
                beenVisited = neighbor.visited;
            if ((movingPoints != INFINITY) && (gScore > movingPoints)) {
                continue;
            }

            if ((!beenVisited) || (gScore < neighbor.g)) {
                neighbor.visited = true;
                neighbor.preNodes.length = 0;
                neighbor.preNodes.push(curNode);
                neighbor.h = neighbor.h || neighbor.heuristic(end, astarHeuristicMode, start);
                neighbor.g = gScore;
                neighbor.f = neighbor.g + neighbor.h;
                if (isPathSearch) {
                    neighbor.closerH = neighbor.h || neighbor.heuristic(end, 0);
                    isNeighborMoreCloser = (neighbor.closerH < closestNode.closerH) ||
                        ((neighbor.closerH === closestNode.closerH) && (neighbor.g < closestNode.g));

                    if (isNeighborMoreCloser) {
                        closestNode = neighbor;
                    }
                }

                if (!beenVisited) {
                    gOpenHeap.push(neighbor);
                } else {
                    gOpenHeap.rescoreElement(neighbor);
                }
            } else if (shortestPathEnable && (gScore == neighbor.g)) {
                neighbor.preNodes.push(curNode);
            } else {
            }
        }

    }

    nodeManager.closestNode = (isPathSearch) ? closestNode : null;
    gOpenHeap.clear();
    return this;
}
export default AStarSerach;
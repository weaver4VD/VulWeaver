import GetAngle from '../../math/angle/Between.js';
import RadToDegree from '../../math/RadToDeg.js';

var DirectionBetween = function (tileA, tileB, round) {
    if (round === undefined) {
        round = true;
    }

    var direction;
    switch (this.mode) {
        case 0:
        case 1:
            if (tileA.y === tileB.y) {
                direction = (tileB.x >= tileA.x) ? 0 : 2;
            } else if (tileA.x === tileB.x) {
                direction = (tileB.y >= tileA.y) ? 1 : 3;
            } else if (this.directions === 4) {
                var angle = RadToDegree(GetAngle(tileA.x, tileA.y, tileB.x, tileB.y));
                if (angle < 0) {
                    angle += 360;
                }
                direction = angle / 90;
                if (round) {
                    direction = Math.round(direction);
                }
            } else {
                var dx = tileB.x - tileA.x;
                var dy = tileB.y - tileA.y;
                if (dx === dy) {
                    direction = (dx > 0) ? 4 : 6;
                } else if (dx === -dy) {
                    direction = (dx > 0) ? 7 : 5;
                } else {
                    var angle = RadToDegree(Math.atan2(dy, dx));
                    if (angle < 0) {
                        angle += 360;
                    }
                    var steps = angle / 45;
                    if (round) {
                        steps = Math.round(steps);
                    }

                    if ((steps >= 0) && (steps < 1)) {
                        direction = steps;
                    } else if ((steps >= 1) && (steps < 2)) {
                        direction = (steps + 3);
                    } else if ((steps >= 2) && (steps < 3)) {
                        direction = (steps - 1);
                    } else if ((steps >= 3) && (steps < 4)) {
                        direction = (steps + 2);
                    } else if ((steps >= 4) && (steps < 5)) {
                        direction = (steps - 2);
                    } else if ((steps >= 5) && (steps < 6)) {
                        direction = (steps + 1);
                    } else if ((steps >= 6) && (steps < 7)) {
                        direction = (steps - 3);
                    } else {
                        direction = steps;
                    }
                }
            }
            break;
        case 2:
            break;
    }

    if (direction === this.directions) {
        direction = 0;
    }
    return direction;
}

export default DirectionBetween;


import DistanceBetween from '../../math/distance/DistanceBetween.js';


var CircleToCircle = function (circleA, circleB) {
    return (DistanceBetween(circleA.x, circleA.y, circleB.x, circleB.y) <= (circleA.radius + circleB.radius));
};

export default CircleToCircle;

var GetOppositeDirection = function (tileX, tileY, direction) {
    return oppositeDirectionMap[direction];
}
const oppositeDirectionMap = {
    0: 2,
    1: 3,
    2: 0,
    3: 1,
    4: 6,
    5: 7,
    6: 4,
    7: 5
}
export default GetOppositeDirection;
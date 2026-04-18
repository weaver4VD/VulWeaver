


var OffsetPoint = function (circle, point)
{
    circle.x += point.x;
    circle.y += point.y;

    return circle;
};

export default OffsetPoint;

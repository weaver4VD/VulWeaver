const DegToRad = Phaser.Math.DegToRad;

const RAD180 = DegToRad(180);

var LayoutFaces = function (parent, faces) {
    var backFace = faces.back;
    if (backFace) {
        if (parent.orientation === 0) {
            backFace.transformVerts(0, 0, 0, 0, RAD180, 0);
        } else {
            backFace.transformVerts(0, 0, 0, RAD180, 0, 0);
        }
    }
}

export default LayoutFaces;
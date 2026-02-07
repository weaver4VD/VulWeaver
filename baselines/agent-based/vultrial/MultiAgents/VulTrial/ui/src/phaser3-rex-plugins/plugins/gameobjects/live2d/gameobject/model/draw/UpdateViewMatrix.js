var UpdateViewMatrix = function (model, calcMatrix) {
    var gameObject = model.parent;
    var projectionMatrix = model._globalData.projectionMatrix;

    var matrix = model.viewMatrix;
    matrix.loadIdentity();
    var modelWidth = gameObject.width;
    var modelHeight = gameObject.height;
    var canvasWidth = projectionMatrix.width;
    var canvasHeight = projectionMatrix.height

    var scaleX = (calcMatrix.scaleX * modelWidth) / canvasWidth;
    var scaleY = (calcMatrix.scaleY * modelHeight) / canvasHeight;

    if (modelWidth > modelHeight) {
        scaleY *= modelWidth / modelHeight;
    } else {
        scaleX *= modelHeight / modelWidth;
    }

    matrix.scale(scaleX, scaleY);
    matrix.rotate(-calcMatrix.rotationNormalized);
    matrix.translate(
        projectionMatrix.toLocalX(calcMatrix.getX(0, 0)),
        projectionMatrix.toLocalY(calcMatrix.getY(0, 0))
    );

    var modelMatrix = model._modelMatrix;
    matrix.multiplyByMatrix(modelMatrix);

    return matrix;
}

export default UpdateViewMatrix;
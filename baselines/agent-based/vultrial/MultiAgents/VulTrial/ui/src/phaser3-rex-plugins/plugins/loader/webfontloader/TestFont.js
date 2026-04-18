const CanvasPool = Phaser.Display.Canvas.CanvasPool;

var TestFont = function (familyName, testString) {
    var canvas = CanvasPool.create();
    var context = canvas.getContext('2d', { willReadFrequently: true });
    var font = `8px ${familyName}`;
    context.font = font;
    var width = Math.ceil(context.measureText(testString).width);
    var baseline = width;
    var height = 2 * baseline;
    if ((width !== canvas.width) || (height !== canvas.height)) {
        canvas.width = width;
        canvas.height = height;
    }
    context.fillStyle = '#000';
    context.fillRect(0, 0, width, height);
    context.textBaseline = 'alphabetic';
    context.fillStyle = '#fff';
    context.font = font;
    context.fillText(testString, 0, baseline);
    var imagedata = context.getImageData(0, 0, width, height).data;
    var hasPixel = false;
    for (var i = 0, cnt = imagedata.length; i < cnt; i += 4) {
        if (imagedata[i] > 0) {
            hasPixel = true;
            break;
        }
    }
    CanvasPool.remove(canvas);
    return hasPixel;
}

export default TestFont;
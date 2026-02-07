import AppendCommandBase from '../../../dynamictext/methods/AppendCommand.js';

var OnParseZoomCameraTag = function (textPlayer, parser, config) {
    var tagName = 'camera.zoom';
    parser
        .on(`+${tagName}`, function (value) {
            AppendCommandBase.call(textPlayer,
                tagName,
                Zoom,
                value,
                textPlayer,
            );
            parser.skipEvent();
        })
        .on(`+${tagName}.to`, function (value, duration, ease) {
            AppendCommandBase.call(textPlayer,
                'camera.zoom.to',
                ZoomTo,
                [value, duration, ease],
                textPlayer,
            );
            parser.skipEvent();
        })
}

var Zoom = function (value) {
    this.targetCamera.setZoom(value);
}

var ZoomTo = function (params) {
    this.targetCamera.zoomTo(...params);
}

export default OnParseZoomCameraTag;
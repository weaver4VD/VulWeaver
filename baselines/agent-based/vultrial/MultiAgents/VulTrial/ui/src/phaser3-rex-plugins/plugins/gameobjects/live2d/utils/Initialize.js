import { CubismFramework, Option } from '../framework/src/live2dcubismframework';
var Initialize = function (config) {
    if (!window.Live2DCubismCore) {
        console.error('live2dcubismcore.js does not load')
    }
    var option = new Option();
    CubismFramework.startUp(option);
    CubismFramework.initialize();
}

export default Initialize;
import Space from '../../space/Space.js';

var CreateSpace = function (scene, data, view, styles, customBuilders) {
    var gameObject = new Space(scene);
    return gameObject;
}

export default CreateSpace;
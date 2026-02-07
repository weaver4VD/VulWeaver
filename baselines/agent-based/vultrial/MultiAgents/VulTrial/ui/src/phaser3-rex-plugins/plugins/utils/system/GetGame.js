import IsGame from './IsGame.js';
import IsSceneObject from './IsSceneObject.js';

var GetGame = function (object) {
    if ((object == null) || (typeof (object) !== 'object')) {
        return null;
    } else if (IsGame(object)) {
        return object;
    } else if (IsGame(object.game)) {
        return object.game;
    } else if (IsSceneObject(object)) {
        return object.sys.game;
    } else if (IsSceneObject(object.scene)) {
        return object.scene.sys.game;
    }
}

export default GetGame;
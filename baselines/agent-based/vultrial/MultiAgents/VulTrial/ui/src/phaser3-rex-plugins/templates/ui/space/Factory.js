import Space from './Space.js';
import ObjectFactory from '../ObjectFactory.js';
import SetValue from '../../../plugins/utils/object/SetValue.js';

ObjectFactory.register('space', function () {
    var gameObject = new Space(this.scene);
    return gameObject;
});

SetValue(window, 'RexPlugins.UI.Space', Space);

export default Space;
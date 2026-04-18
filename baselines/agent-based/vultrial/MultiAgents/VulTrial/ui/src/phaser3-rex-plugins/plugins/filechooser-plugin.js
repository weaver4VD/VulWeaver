import OpenFileChooser from './behaviors/filechooser/Open.js';
import Factory from './gameobjects/dom/filechooser/Factory.js';
import Creator from './gameobjects/dom/filechooser/Creator.js';
import FileChooser from './gameobjects/dom/filechooser/FileChooser.js';
import SetValue from './utils/object/SetValue.js';

class FileChooserPlugin extends Phaser.Plugins.BasePlugin {

    constructor(pluginManager) {
        super(pluginManager);
        pluginManager.registerGameObject('rexFileChooser', Factory, Creator);
    }

    start() {
        var eventEmitter = this.game.events;
        eventEmitter.on('destroy', this.destroy, this);
    }
    open(config) {
        return OpenFileChooser(this.game, config);
    }
}

SetValue(window, 'RexPlugins.GameObjects.FileChooser', FileChooser);

export default FileChooserPlugin;
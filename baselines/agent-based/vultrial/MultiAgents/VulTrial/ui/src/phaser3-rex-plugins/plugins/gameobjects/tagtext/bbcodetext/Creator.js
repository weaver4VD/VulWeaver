import BBCodeText from './BBCodeText.js';

const GetAdvancedValue = Phaser.Utils.Objects.GetAdvancedValue;
const BuildGameObject = Phaser.GameObjects.BuildGameObject;

export default function (config, addToScene) {
    if (config === undefined) { config = {}; }
    if (addToScene !== undefined) {
        config.add = addToScene;
    }

    var content = GetAdvancedValue(config, 'text', '');
    var style = GetAdvancedValue(config, 'style', null);

    var padding = GetAdvancedValue(config, 'padding', null);

    if (padding !== null) {
        style.padding = padding;
    }

    var gameObject = new BBCodeText(this.scene, 0, 0, content, style);
    BuildGameObject(this.scene, gameObject, config);

    gameObject.autoRound = GetAdvancedValue(config, 'autoRound', true);

    return gameObject;
};
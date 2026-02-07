import InputRow from '../gameobjects/inputrow/InputRow.js';
import CreateBackground from '../../utils/build/CreateBackground.js';
import CreateTitleLabel from './CreateTitleLabel.js';
import CreateInputField from './CreateInputField.js';

const GetValue = Phaser.Utils.Objects.GetValue;

var CreateInputRow = function (scene, config, style) {
    var titleStyle = GetValue(style, 'title') || {};
    var inputTitle = CreateTitleLabel(scene, config, titleStyle);
    var inputField = CreateInputField(scene, config, style);
    var backgroundStyle = GetValue(style, 'background') || {};
    var background = CreateBackground(scene, backgroundStyle);

    var inputRow = new InputRow(scene, {
        ...config,
        ...style,

        inputTitle: inputTitle,
        inputField: inputField,
        background: background,
    });
    scene.add.existing(inputRow);

    inputRow.setTitle(config);

    return inputRow;
}

export default CreateInputRow;
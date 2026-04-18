import {
    ElementProperties,
    StyleProperties,
} from './InputTextProperties.js';
import SetPrpoerties from '../../../gameobjects/dom/utils/SetProperties.js';
import StopPropagationTouchEvents from '../../../gameobjects/dom/utils/StopPropagationTouchEvents.js';

const GetValue = Phaser.Utils.Objects.GetValue;

var CreateElement = function (parent, config) {
    var element;
    var textType = GetValue(config, 'inputType', undefined);
    if (textType === undefined) {
        textType = GetValue(config, 'type', 'text');
    }
    if (textType === 'textarea') {
        element = document.createElement('textarea');
        element.style.resize = 'none';
    } else {
        element = document.createElement('input');
        element.type = textType;
    }

    var style = GetValue(config, 'style', undefined);
    var elementStyle = element.style;
    SetPrpoerties(StyleProperties, style, elementStyle);
    elementStyle.position = 'absolute';
    elementStyle.opacity = 0;
    elementStyle.pointerEvents = 'none';
    elementStyle.zIndex = 0;
    elementStyle.transform = 'scale(0)';

    SetPrpoerties(ElementProperties, config, element);
    StopPropagationTouchEvents(element);
    var scaleManager = parent.scene.sys.scale;
    var parentElement = (scaleManager.isFullscreen) ? scaleManager.fullscreenTarget : document.body;
    parentElement.appendChild(element);

    return element;
}

export default CreateElement;
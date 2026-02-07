import Base from '../../scrollbar/ScrollBar.js';
import Clone from '../../../../plugins/utils/object/Clone.js'

class Slider extends Base {
    constructor(scene, config) {
        if (config === undefined) {
            config = {};
        }

        var sliderConfig = Clone(config);
        config = {
            slider: sliderConfig
        }
        config.orientation = sliderConfig.orientation;
        delete sliderConfig.orientation;
        config.background = sliderConfig.background;
        delete sliderConfig.background;
        config.buttons = sliderConfig.buttons;
        delete sliderConfig.buttons;

        super(scene, config);

        var slider = this.childrenMap.slider;
        this.addChildrenMap('track', slider.childrenMap.track);
        this.addChildrenMap('indicator', slider.childrenMap.indicator);
        this.addChildrenMap('thumb', slider.childrenMap.thumb);
    }
}

export default Slider;
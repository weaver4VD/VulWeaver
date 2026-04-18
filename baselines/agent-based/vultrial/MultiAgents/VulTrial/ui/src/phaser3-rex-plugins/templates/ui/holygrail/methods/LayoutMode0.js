

import {
    GetAddHeaderConfig,
    GetAddLeftSideConfig, GetAddContentConfig, GetAddRightSideConfig,
    GetAddFooterConfig,
    GetAddContainerConfig
} from './GetAddChildConfig.js';
import CreatExpandContainer from './CreatExpandContainer.js';

var LayoutMode0 = function (config) {
    var scene = this.scene;
    var header = config.header;
    if (header) {
        this.add(header, GetAddHeaderConfig(config));
    }

        
    var bodySizer = CreatExpandContainer(scene, 0);
    this.add(bodySizer, GetAddContainerConfig(config));
    var leftSide = config.leftSide;
    if (leftSide) {
        bodySizer.add(leftSide, GetAddLeftSideConfig(config));
    }
    var content = config.content;
    if (content) {
        bodySizer.add(content, GetAddContentConfig(config));
    }
    var rightSide = config.rightSide;
    if (rightSide) {
        bodySizer.add(rightSide, GetAddRightSideConfig(config));
    }
    var footer = config.footer;
    if (footer) {
        this.add(footer, GetAddFooterConfig(config));
    }
}

export default LayoutMode0;
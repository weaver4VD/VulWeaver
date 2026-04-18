

import {
    GetAddHeaderConfig,
    GetAddLeftSideConfig, GetAddContentConfig, GetAddRightSideConfig,
    GetAddFooterConfig,
    GetAddContainerConfig
} from './GetAddChildConfig.js';
import CreatExpandContainer from './CreatExpandContainer.js';

var LayoutMode1 = function (config) {
    var scene = this.scene;
    var header = config.header;
    if (header) {
        this.add(header, GetAddHeaderConfig(config));
    }

    
    var bodySizer0 = CreatExpandContainer(scene, 0);
    this.add(bodySizer0, GetAddContainerConfig(config));
    var leftSide = config.leftSide;
    if (leftSide) {
        bodySizer0.add(leftSide, GetAddLeftSideConfig(config));
    }

    
    var bodySizer1 = CreatExpandContainer(scene, 1);
    bodySizer0.add(bodySizer1, GetAddContainerConfig(config));

    
    var bodySizer2 = CreatExpandContainer(scene, 0);
    bodySizer1.add(bodySizer2, GetAddContainerConfig(config));
    var content = config.content;
    if (content) {
        bodySizer2.add(content, GetAddContentConfig(config));
    }
    var rightSide = config.rightSide;
    if (rightSide) {
        bodySizer2.add(rightSide, GetAddRightSideConfig(config));
    }
    var footer = config.footer;
    if (footer) {
        bodySizer1.add(footer, GetAddFooterConfig(config));
    }
}

export default LayoutMode1;
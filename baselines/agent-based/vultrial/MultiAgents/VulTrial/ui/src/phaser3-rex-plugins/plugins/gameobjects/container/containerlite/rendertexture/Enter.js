import Exit from './Exit.js';
import Snapshot from '../../../../utils/rendertexture/Snapshot.js';

var Enter = function (parentContainer, rtOwner) {
    if (!parentContainer) {
        return false;
    }

    Exit(parentContainer, rtOwner);
    var useParentBounds = rtOwner.useParentBounds;
    Snapshot({
        gameObjects: parentContainer.getAllVisibleChildren(),
        renderTexture: rtOwner.rt,
        x: rtOwner.x,
        y: rtOwner.y,
        width: ((useParentBounds) ? parentContainer.displayWidth : undefined),
        height: ((useParentBounds) ? parentContainer.displayHeighth : undefined),
        originX: ((useParentBounds) ? parentContainer.originX : undefined),
        originY: ((useParentBounds) ? parentContainer.originY : undefined),
    });
    parentContainer.setChildVisible(rtOwner, true);
    var visibleSibling = rtOwner.visibleSibling;
    var children = parentContainer.children;
    for (var i = 0, cnt = children.length; i < cnt; i++) {
        var child = children[i];
        if ((child.visible) && (child !== rtOwner)) {
            parentContainer.setChildVisible(child, false);
            visibleSibling.push(child);
        }
    }

    rtOwner.isRunning = true;

    return true;
}

export default Enter;
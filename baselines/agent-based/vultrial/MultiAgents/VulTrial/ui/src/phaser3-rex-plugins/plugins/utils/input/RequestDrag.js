import IsPointerInHitArea from './IsPointerInHitArea.js';

var RequestDrag = function (gameObject) {
    var inputPlugin = gameObject.scene.input;
    var inputManager = inputPlugin.manager;
    var pointersTotal = inputManager.pointersTotal;
    var pointers = inputManager.pointers,
        pointer;
    for (var i = 0; i < pointersTotal; i++) {
        pointer = pointers[i];
        if (
            (!pointer.primaryDown) ||
            (inputPlugin.getDragState(pointer) !== 0) ||
            (!IsPointerInHitArea(gameObject, pointer))
        ) {
            continue;
        }
        inputPlugin.setDragState(pointer, 1);
        inputPlugin._drag[pointer.id] = [gameObject];
        if ((inputPlugin.dragDistanceThreshold === 0) || (inputPlugin.dragTimeThreshold === 0)) {
            inputPlugin.setDragState(pointer, 3);
            inputPlugin.processDragStartList(pointer);
        } else {
            inputPlugin.setDragState(pointer, 2);
        }

        return true;
    }

    return false;
}

export default RequestDrag;
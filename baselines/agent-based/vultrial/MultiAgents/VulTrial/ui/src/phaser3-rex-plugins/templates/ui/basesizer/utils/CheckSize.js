var CheckSize = function (child, parent) {
    if (child.width < child.childrenWidth) {
        console.warn(`Layout width error: Parent=${parent.constructor.name}, Child=${child.constructor.name}`);
    }
    if (child.height < child.childrenHeight) {
        console.warn(`Layout height error: Parent=${parent.constructor.name}, Child=${child.constructor.name}`);
    }
}

export default CheckSize;
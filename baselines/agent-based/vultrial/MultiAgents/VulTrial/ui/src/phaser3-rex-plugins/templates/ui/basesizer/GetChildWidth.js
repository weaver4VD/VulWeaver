import { GetDisplayWidth } from '../../../plugins/utils/size/GetDisplaySize.js';

var GetChildWidth = function (child) {
    var childWidth;
    if (child.isRexSizer) {
        childWidth = Math.max(child.minWidth, child.childrenWidth);
    } else {
        if (child.minWidth !== undefined) {
            childWidth = child.minWidth;
        } else {
            childWidth = GetDisplayWidth(child);
        }
    }

    return childWidth;
}

export default GetChildWidth;
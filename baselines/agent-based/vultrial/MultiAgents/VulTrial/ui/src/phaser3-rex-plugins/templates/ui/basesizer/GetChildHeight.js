import { GetDisplayHeight } from '../../../plugins/utils/size/GetDisplaySize.js';

var GetChildHeight = function (child) {
    var childHeight;
    if (child.isRexSizer) {
        childHeight = Math.max(child.minHeight, child.childrenHeight);
    } else {
        if (child.minHeight !== undefined) {
            childHeight = child.minHeight;
        } else {
            childHeight = GetDisplayHeight(child);
        }
    }
    return childHeight;
}

export default GetChildHeight;
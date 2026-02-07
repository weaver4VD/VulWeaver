import { Repeat } from '../../../nodes';
import IsPlainObject from '../../../../../utils/object/IsPlainObject.js';



var CreateRepeatNode = function (data, child) {
    if (IsPlainObject(data)) {
        data.child = child;
    } else {
        data = {
            maxLoop: data,
            child: child
        }
    }
    return new Repeat(data);
}

export default CreateRepeatNode;
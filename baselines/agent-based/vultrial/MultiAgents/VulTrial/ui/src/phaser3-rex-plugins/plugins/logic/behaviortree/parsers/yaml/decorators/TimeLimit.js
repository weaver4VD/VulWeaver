import { TimeLimit } from '../../../nodes';
import IsPlainObject from '../../../../../utils/object/IsPlainObject.js';



var CreateTimeLimitNode = function (data, child) {
    if (IsPlainObject(data)) {
        data.child = child;
    } else {
        data = {
            duration: data,
            child: child
        }
    }
    return new TimeLimit(data);
}

export default CreateTimeLimitNode;
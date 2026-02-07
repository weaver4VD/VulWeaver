import { RepeatUntilSuccess } from '../../../nodes';
import IsPlainObject from '../../../../../utils/object/IsPlainObject.js';



var CreateRepeatUntilSuccessNode = function (data, child) {
    if (IsPlainObject(data)) {
        data.child = child;
    } else {
        data = {
            maxLoop: data,
            child: child
        }
    }
    return new RepeatUntilSuccess(data)
}

export default CreateRepeatUntilSuccessNode;
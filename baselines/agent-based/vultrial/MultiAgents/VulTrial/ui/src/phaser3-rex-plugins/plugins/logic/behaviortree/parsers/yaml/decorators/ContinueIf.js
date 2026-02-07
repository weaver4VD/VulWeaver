import { ContinueIf } from '../../../nodes';
import IsPlainObject from '../../../../../utils/object/IsPlainObject.js';



var CreateContinueIfNode = function (data, child) {
    if (IsPlainObject(data)) {
        data.child = child;
    } else {
        data = {
            expression: data,
            child: child
        }
    }
    return new ContinueIf(data);
}

export default CreateContinueIfNode;
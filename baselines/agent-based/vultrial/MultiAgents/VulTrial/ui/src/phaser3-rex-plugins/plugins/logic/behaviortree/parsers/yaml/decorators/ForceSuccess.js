import { ForceSuccess } from '../../../nodes';



var CreateForceSuccessNode = function (data, child) {
    if (IsPlainObject(data)) {
        data.child = child;
    } else {
        data = {
            child: child
        }
    }
    return new ForceSuccess(data);
}

export default CreateForceSuccessNode;
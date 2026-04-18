import { ForceFailure } from '../../../nodes';



var CreateForceFailureNode = function (data, child) {
    if (IsPlainObject(data)) {
        data.child = child;
    } else {
        data = {
            child: child
        }
    }
    return new ForceFailure(data);
}

export default CreateForceFailureNode;
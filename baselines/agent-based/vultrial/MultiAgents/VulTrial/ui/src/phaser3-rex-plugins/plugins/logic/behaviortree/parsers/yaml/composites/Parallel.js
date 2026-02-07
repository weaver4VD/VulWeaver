import { Parallel } from '../../../nodes';



var CreateParallelNode = function (data) {
    return new Parallel(data);
}

export default CreateParallelNode;
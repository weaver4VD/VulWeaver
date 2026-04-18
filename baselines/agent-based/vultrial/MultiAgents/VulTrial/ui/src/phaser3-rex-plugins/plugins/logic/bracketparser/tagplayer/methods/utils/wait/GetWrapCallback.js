import { RemoveWaitEvents } from '../Events.js';

var GetWrapCallback = function (tagPlayer, callback, args, scope, removeFrom) {
    return function () {
        tagPlayer.emit(RemoveWaitEvents, removeFrom);
        callback.apply(scope, args);
    }
}
export default GetWrapCallback;
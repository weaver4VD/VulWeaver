import { RemoveWaitEvents } from '../Events.js';

var GetWrapCallback = function (textPlayer, callback, args, scope, removeFrom) {
    return function () {
        textPlayer.emit(RemoveWaitEvents, removeFrom);
        callback.apply(scope, args);
    }
}
export default GetWrapCallback;
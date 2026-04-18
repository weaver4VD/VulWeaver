import GetWrapCallback from './GetWrapCallback.js';
import { RemoveWaitEvents } from '../Events.js';

var IsWaitGameObject = function (tagPlayer, name) {
    var names = name.split('.');
    return tagPlayer.gameObjectManagers.hasOwnProperty(names[0]);
}

var WaitGameObject = function (tagPlayer, tag, callback, args, scope) {
    var wrapCallback = GetWrapCallback(tagPlayer, callback, args, scope);
    var tags = tag.split('.');
    var goType = tags[0];
    var gameObjectManager = tagPlayer.getGameObjectManager(goType);
    var waitEventName = `wait.${goType}`
    switch (tags.length) {
        case 1:
            if (gameObjectManager.isEmpty) {
                tagPlayer.emit(waitEventName);
                wrapCallback();
            } else {
                tagPlayer.once(RemoveWaitEvents, function (removeFrom) {
                    gameObjectManager.off('empty', wrapCallback, tagPlayer);
                });
                gameObjectManager.once('empty', wrapCallback, tagPlayer);
                tagPlayer.emit(waitEventName);
            }
            return;

        case 2:
            var name = tags[1];
            if (!gameObjectManager.has(name)) {
                tagPlayer.emit(waitEventName, name);
                wrapCallback();
            } else {
                var spriteData = gameObjectManager.get(name);
                var gameObject = spriteData.gameObject;
                tagPlayer.once(RemoveWaitEvents, function () {
                    gameObject.off('destroy', wrapCallback, tagPlayer);
                });

                gameObject.once('destroy', wrapCallback, tagPlayer);
                tagPlayer.emit(waitEventName, name);
            }
            return;

        case 3:
            var name = tags[1],
                prop = tags[2];
            if (gameObjectManager.isNumberProperty(name, prop)) {
                var task = gameObjectManager.getTweenTask(name, prop);
                if (!task) {
                    tagPlayer.emit(waitEventName, name, prop);
                    wrapCallback();
                } else {
                    tagPlayer.once(RemoveWaitEvents, function () {
                        task.off('complete', wrapCallback, tagPlayer);
                    });

                    task.once('complete', wrapCallback, tagPlayer);
                    tagPlayer.emit(waitEventName, name, prop);
                }
                return;
            }

            var dataKey = prop;
            var matchFalseFlag = dataKey.startsWith('!');
            if (matchFalseFlag) {
                dataKey = dataKey.substring(1);
            }
            if (gameObjectManager.hasData(name, dataKey)) {
                var gameObject = gameObjectManager.getGO(name);
                var flag = gameObject.getData(dataKey);
                var matchTrueFlag = !matchFalseFlag;
                if (flag === matchTrueFlag) {
                    tagPlayer.emit(waitEventName, name, prop);
                    wrapCallback();
                } else {
                    var eventName = `changedata-${dataKey}`;
                    var callback = function (gameObject, value, previousValue) {
                        value = !!value;
                        if (value === matchTrueFlag) {
                            wrapCallback.call(tagPlayer);
                        }
                    }
                    tagPlayer.once(RemoveWaitEvents, function () {
                        gameObject.off(eventName, callback);
                    });

                    gameObject.on(eventName, callback);
                    tagPlayer.emit(waitEventName, name, prop);
                }
                return;
            }

    }

}


export { IsWaitGameObject, WaitGameObject };
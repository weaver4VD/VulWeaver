var IsInValidKey = function (keys) {
    return (keys == null) || (keys === '') || (keys.length === 0);
};

var GetEntry = function (target, keys, defaultEntry) {
    var entry = target;
    if (IsInValidKey(keys)) {
    } else {
        if (typeof (keys) === 'string') {
            keys = keys.split('.');
        }

        var key;
        for (var i = 0, cnt = keys.length; i < cnt; i++) {
            key = keys[i];
            if ((entry[key] == null) || (typeof (entry[key]) !== 'object')) {
                var newEntry;
                if (i === cnt - 1) {
                    if (defaultEntry === undefined) {
                        newEntry = {};
                    } else {
                        newEntry = defaultEntry;
                    }
                } else {
                    newEntry = {};
                }

                entry[key] = newEntry;
            }

            entry = entry[key];
        }
    }

    return entry;
};

var SetValue = function (target, keys, value, delimiter) {
    if (delimiter === undefined) {
        delimiter = '.';
    }
    if (typeof (target) !== 'object') {
        return;
    }
    else if (IsInValidKey(keys)) {
        if (value == null) {
            return;
        }
        else if (typeof (value) === 'object') {
            target = value;
        }
    } else {
        if (typeof (keys) === 'string') {
            keys = keys.split(delimiter);
        }

        var lastKey = keys.pop();
        var entry = GetEntry(target, keys);
        entry[lastKey] = value;
    }

    return target;
};

export default SetValue;
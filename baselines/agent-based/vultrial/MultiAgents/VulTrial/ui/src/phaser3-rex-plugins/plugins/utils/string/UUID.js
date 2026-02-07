


const HasBuiltRandomUUID = (window.crypto && window.crypto.randomUUID);

var UUID = function () {
    if (HasBuiltRandomUUID) {
        return window.crypto.randomUUID();
    }

    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = Math.random() * 16 | 0;
        var v = (c === 'x') ? r : (r & 0x3 | 0x8);

        return v.toString(16);
    });
};

export default UUID;

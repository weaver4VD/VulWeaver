import Clear from './Clear.js';


var Clone = function (obj, out) {
    var objIsArray = Array.isArray(obj);

    if (out === undefined) {
        out = (objIsArray) ? [] : {};
    } else {
        Clear(out);
    }

    if (objIsArray) {
        out.length = obj.length;
        for (var i = 0, cnt = obj.length; i < cnt; i++) {
            out[i] = obj[i];
        }
    } else {
        for (var key in obj) {
            out[key] = obj[key];
        }
    }

    return out;
};

export default Clone;

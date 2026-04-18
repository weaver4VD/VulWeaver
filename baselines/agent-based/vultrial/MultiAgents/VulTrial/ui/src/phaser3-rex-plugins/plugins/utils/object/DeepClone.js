import IsPlainObject from './IsPlainObject.js';

var DeepClone = function (inObject) {
    var outObject;
    var value;
    var key;

    if ((inObject == null) || (typeof inObject !== 'object')) {
        return inObject;
    }
    outObject = Array.isArray(inObject) ? [] : {};

    if (IsPlainObject(inObject)) {
        for (key in inObject) {
            value = inObject[key];
            outObject[key] = DeepClone(value);
        }

    } else {
        outObject = inObject;
    }

    return outObject;
};

export default DeepClone;
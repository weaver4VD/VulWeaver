import GetGraphItem from './GetGraphItem.js';
import ObjBank from './ObjBank.js';
import IsUID from './IsUID.js';

const uidKey = ObjBank.uidKey;
var GetObjUID = function (gameObject) {
    var uid;
    if (IsUID(gameObject)) {
        uid = gameObject;
    } else {
        uid = GetGraphItem(gameObject)[uidKey];
    }
    return uid;
}
export default GetObjUID;
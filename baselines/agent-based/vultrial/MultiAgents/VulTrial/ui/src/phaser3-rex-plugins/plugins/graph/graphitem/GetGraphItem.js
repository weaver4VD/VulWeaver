import ObjBank from './ObjBank.js';
import GraphItemData from './GraphItemData.js';
import IsUID from './IsUID.js';

var GetGraphItem = function (gameObject) {
    if (IsUID(gameObject)) {
        return ObjBank.get(gameObject);
    } else {
        if (!gameObject.hasOwnProperty('rexGraphItem')) {
            gameObject.rexGraphItem = new GraphItemData(gameObject);
        }
        return gameObject.rexGraphItem;
    }
}
export default GetGraphItem;
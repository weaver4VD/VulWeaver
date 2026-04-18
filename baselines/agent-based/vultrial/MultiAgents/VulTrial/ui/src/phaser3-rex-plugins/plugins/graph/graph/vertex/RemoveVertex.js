import GetGraphItem from '../../graphitem/GetGraphItem.js';

var RemoveVertex = function (gameObejct, destroy, removeEdge) {
    if (!this.isVertex(gameObejct)) {
        return this;
    }
    
    if (destroy === undefined) {
        destroy = false;
    }
    if (removeEdge === undefined) {
        removeEdge = true;
    }

    var uid = this.getObjUID(gameObejct);
    if (removeEdge) {
        var vertex = this.getVertexData(uid);
        for (var edgeUid in vertex) {
            this.removeEdge(edgeUid, destroy);
        }
    }
    delete this.vertices[uid];
    this.vertexCount--;
    GetGraphItem(gameObejct).setGraph(null);
    if (destroy && gameObejct.destroy) {
        gameObject.destroy();
    }

    return this;
}

export default RemoveVertex;
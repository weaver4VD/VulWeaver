var IsEdge = function (gameObejct) {
    var uid = this.getObjUID(gameObejct);
    return this.edges.hasOwnProperty(uid);
}

export default IsEdge;
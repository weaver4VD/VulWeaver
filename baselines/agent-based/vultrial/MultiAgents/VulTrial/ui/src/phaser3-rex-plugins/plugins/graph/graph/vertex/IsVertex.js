var IsVertex = function (gameObejct) {
    var uid = this.getObjUID(gameObejct);
    return this.vertices.hasOwnProperty(uid);
}

export default IsVertex;
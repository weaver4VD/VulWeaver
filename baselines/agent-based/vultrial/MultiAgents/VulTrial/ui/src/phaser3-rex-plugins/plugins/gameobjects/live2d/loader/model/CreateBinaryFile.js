const BinaryFile = Phaser.Loader.FileTypes.BinaryFile;

var CreateBinaryFile = function (loader, key, url, xhrSettings, dataKey) {
    var file = new BinaryFile(loader, key, url, xhrSettings);
    file.dataKey = dataKey;
    file.cache = false;
    return file;
}

export default CreateBinaryFile;
import Uint8ArrayReader from '../../utils/arraybuffers/Uint8ArrayReader.js';

var GetChunkEndByteIndex = function (pngBuffer, chunkType) {
    var reader;
    if (pngBuffer instanceof (Uint8ArrayReader)) {
        reader = pngBuffer;
    } else {
        reader = new Uint8ArrayReader(pngBuffer);
    }

    reader.seek(8);
    while (!reader.outOfArray) {
        var dataLength = reader.readUint32(true);
        if (chunkType === reader.readString(4)) {
            return reader.pointer + dataLength + 4;
        } else {
            reader.seekForward(dataLength + 4);
        }
    }

    return -1;
}



export default GetChunkEndByteIndex;
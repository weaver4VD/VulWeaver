import GetChunkEndByteIndex from './GetChunkEndByteIndex.js';
import Uint8ArrayReader from '../../utils/arraybuffers/Uint8ArrayReader.js';

var ExtractData = function (pngBuffer) {
    var reader = new Uint8ArrayReader(pngBuffer);
    var pngByteLength = GetChunkEndByteIndex(reader, 'IEND');
    reader.seek(pngByteLength);
    if (reader.outOfArray) {
        return null;
    }
    var header0 = reader.readUint32();
    var dataType = header0 & 0xf;
    var header1 = reader.readUint32();
    var data = reader.readUint8Array();
    if (dataType === 0) {
        if (data.length === 0) {
            return null;
        } else {
            data = (new TextDecoder()).decode(data);
            data = JSON.parse(data);
        }
    }

    return data;
}

export default ExtractData;
import GetChunkEndByteIndex from './GetChunkEndByteIndex.js';
import Uint8ArrayWriter from '../../utils/arraybuffers/Uint8ArrayWriter.js';

var AppendData = function (pngBuffer, data) {
    var pngByteLength = GetChunkEndByteIndex(pngBuffer, 'IEND');

    var isUint8Array = (typeof (obj) === 'object') && (obj.constructor === Uint8Array);
    var dataType = (isUint8Array) ? 1 : 0;
    var header0 = dataType;
    var header1 = 0;

    var dataUint8Array;
    if (isUint8Array) {
        dataUint8Array = data;
    } else {
        if (data != null) {
            data = JSON.stringify(data);
            dataUint8Array = (new TextEncoder()).encode(data);
        } else {
            dataUint8Array = new Uint8Array(0);
        }
    }
    var outputLength = pngByteLength + 8 + dataUint8Array.length;
    var writer = (new Uint8ArrayWriter(outputLength))
        .writeUint8Array(pngBuffer.slice(0, pngByteLength))
        .writeUint32(header0)
        .writeUint32(header1)
        .writeUint8Array(dataUint8Array)

    return writer.buf;
}

export default AppendData;
import LoadHeader from './LoadHeader.js';

var Save = function (fileID, header, content, updateMode) {
    if (typeof (content) === 'boolean') {
        updateMode = content;
        content = undefined;
    }
    if (updateMode === undefined) {
        updateMode = false;
    }

    var userID = this.userID;
    if (header === undefined) {
        header = {};
    }
    header.userID = userID;
    header.fileID = fileID;
    header.type = 'header';

    if (content) {
        content.userID = userID;
        content.fileID = fileID;
        content.type = 'content';
    }
    var writeCommand = (updateMode) ? 'update' : 'set';

    var self = this;
    return LoadHeader.call(this, fileID)
        .then(function (prevHeader) {
            var headerDocRef, contentDocRef;
            if (prevHeader) {
                headerDocRef = self.rootRef.doc(prevHeader.headerDocID);
                if (content) {
                    if (prevHeader.contentDocID) {
                        contentDocRef = self.rootRef.doc(prevHeader.contentDocID);
                    } else {
                        contentDocRef = self.rootRef.doc();
                    }
                }
            } else {
                headerDocRef = self.rootRef.doc();
                if (content) {
                    contentDocRef = self.rootRef.doc();
                }
            }
            if (header.hasOwnProperty('headerDocID')) {
                delete header.headerDocID;
            }
            if (contentDocRef) {
                header.contentDocID = contentDocRef.id;
            }


            var batch = self.database.batch();
            batch[writeCommand](headerDocRef, header);
            if (content) {
                batch[writeCommand](contentDocRef, content);
            }
            return batch.commit();
        })
        .then(function () {
            return Promise.resolve({
                userID: userID,
                fileID: fileID
            });
        })
        .catch(function (error) {
            return Promise.reject({
                error: error,
                userID: userID,
                fileID: fileID
            });
        });
}

export default Save;
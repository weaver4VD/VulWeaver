var Methods = {
    startReceiving() {
        var query = this.getReceiverQuery(this.receiverID).orderBy('timestamp', 'desc').limit(1);
        var self = this;
        this.unsubscribe = query.onSnapshot(
            {
                includeMetadataChanges: true
            },
            function (querySnapshot) {
                if (querySnapshot.size > 0) {
                    var doc = querySnapshot.docs[0];
                    if (doc.metadata.hasPendingWrites) {
                        if (self.skipFirst) {
                            self.skipFirst = false;
                        }
                        return;
                    }

                    self.resetPageQuery(self.receiverID, doc);

                    if (self.skipFirst) {
                        self.skipFirst = false;
                    } else {
                        var d = DocToMessage(doc);
                        self.cacheMessages.push(d);
                        self.emit('receive', d);
                    }
                } else {
                    if (self.skipFirst) {
                        self.skipFirst = false;
                    }
                }
            },
            function (error) {
                debugger
            }
        )

        return this;
    },

    stopReceiving() {
        if (this.unsubscribe) {
            this.unsubscribe();
        }
        this.resetQueryFlag = true;
        this.cacheMessages.length = 0;
        return this;
    },

    loadPreviousMessages() {
        this.resetPageQuery(this.receiverID);

        var self = this;
        return this.page.loadNextPage()
            .then(function (docs) {
                var messages = [];
                for (var i = 0, cnt = docs.length; i < cnt; i++) {
                    messages.push(DocToMessage(docs[i]));
                }

                self.cacheMessages.splice(0, 0, ...messages);
                return Promise.resolve(messages);
            })
    },

    resetPageQuery(receiverID, baselineDoc) {
        if (!this.resetQueryFlag) {
            return this;
        }

        this.resetQueryFlag = false;
        var baselineMode = (this.skipFirst) ? 'startAt' : 'startAfter';
        this.page
            .setBaselineDoc(baselineDoc, baselineMode)
            .setQuery(this.getPageQuery(receiverID));
        return this;
    }
}

var DocToMessage = function (doc) {
    var message = doc.data();
    message.timestamp = message.timestamp.seconds * 1000;
    return message;
}

export default Methods;
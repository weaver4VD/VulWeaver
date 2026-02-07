import Load from '../utils/query/Load.js';

var LoadPreviousPage = function () {
    if ((this.pageIndex === undefined) || (this.pageIndex === 1)) {
        return this.loadFirstPage();
    }

    var callback = (this.dataMode === 0) ? LoadStaticPage : LoadDynamicPage;
    return callback.call(this);
}

var LoadStaticPage = function () {
    var self = this;
    return Load(this.prevQuery, (this.itemCount + 1), 0, this.currPageStartDocRef, 'startAfter')
        .then(function (docs) {
            var docCount = docs.length - 1;
            self.cacheItems = docs;
            self.cacheItems.pop();
            self.cacheItems.reverse();
            self.pageIndex -= 1;
            self.endItemIndex = self.startItemIndex - 1;
            self.startItemIndex = self.endItemIndex - docCount + 1;
            self.isFullPage = (docCount === self.itemCount);
            self.prevPageEndDocRef = docs[docCount];
            self.currPageStartDocRef = docs[docCount - 1];
            self.currPageEndDocRef = docs[0];
            return Promise.resolve(self.cacheItems);
        })
}

var LoadDynamicPage = function () {
    var skip = (this.pageIndex - 1) * this.itemCount;
    var self = this;
    return Load(this.nextQuery, this.itemCount, skip, this.baselineDocRef, this.baselineMode)
        .then(function (docs) {
            var docCount = docs.length;
            self.cacheItems = docs;
            self.pageIndex -= 1;
            self.endItemIndex = self.startItemIndex - 1;
            self.startItemIndex = self.endItemIndex - docCount + 1;
            self.isFullPage = (docCount === self.itemCount);
            return Promise.resolve(self.cacheItems);
        })
}

export default LoadPreviousPage;
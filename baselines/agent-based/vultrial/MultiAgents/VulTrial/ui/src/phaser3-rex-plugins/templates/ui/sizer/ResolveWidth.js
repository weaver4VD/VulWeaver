import ResolveWidthBase from '../basesizer/ResolveWidth.js';

var ResolveWidth = function (width) {
    var width = ResolveWidthBase.call(this, width);
    if ((this.proportionLength === undefined) && (this.orientation === 0)) {
        var remainder = width - this.childrenWidth;
        if (remainder > 0) {
            remainder = width - this.getChildrenWidth(false);
            this.proportionLength = remainder / this.childrenProportion;
        } else {
            this.proportionLength = 0;
            if (remainder < 0) {
            }
        }
    }

    return width;
}

export default ResolveWidth;
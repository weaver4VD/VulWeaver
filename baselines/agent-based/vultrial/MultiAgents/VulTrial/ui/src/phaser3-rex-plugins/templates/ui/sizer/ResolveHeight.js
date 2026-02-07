import ResolveHeightBase from '../basesizer/ResolveHeight.js';

var ResolveHeight = function (height) {
    var height = ResolveHeightBase.call(this, height);
    if ((this.proportionLength === undefined) && (this.orientation === 1)) {
        var remainder = height - this.childrenHeight;
        if (remainder > 0) {
            remainder = height - this.getChildrenHeight(false);
            this.proportionLength = remainder / this.childrenProportion;
        } else {
            this.proportionLength = 0;
            if (remainder < 0) {
            }
        }
    }

    return height;
}

export default ResolveHeight;
var Layout = function () {
    var scaleXSave = this.scaleX;
    var scaleYSave = this.scaleY;
    var scale1 = (scaleXSave === 1) && (scaleYSave === 1);
    if (!scale1) {
        this.setScale(1);
    }
    this.runLayout();
    if (!scale1) {
        this.setScale(scaleXSave, scaleYSave);
    }
    return this;
}
export default Layout;
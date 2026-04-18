export default {
    setTint(tint) {
        this.tint = tint;
        this.tintFill = false;
        return this;
    },

    setTintFill(tint) {
        this.tint = tint;
        this.tintFill = true;
        return this;
    },

    clearTint() {
        this.setTint(0xffffff);
        return this;
    }
}
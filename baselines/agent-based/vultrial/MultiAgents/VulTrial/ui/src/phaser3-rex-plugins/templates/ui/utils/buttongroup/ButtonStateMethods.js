
export default {
    clearAllButtonsState() {
        this.buttonGroup.clearAllButtonsState();
        return this;
    },

    getAllButtonsState() {
        return this.buttonGroup.getAllButtonsState();
    },
    setSelectedButtonName(name) {
        this.buttonGroup.setSelectedButtonName(name);
        return this;
    },

    getSelectedButtonName() {
        return this.buttonGroup.getSelectedButtonName();
    },
    setButtonState(name, state) {
        this.buttonGroup.setButtonState(name, state);
        return this;
    },

    getButtonState(name) {
        return this.buttonGroup.getButtonState(name);
    }
}


import GetLocalState from './utils/GetLocalState.js';

export default {
    updateChildVisible(child) {
        var localState = GetLocalState(child);
        var parent = localState.parent;
        var maskVisible = (localState.hasOwnProperty('maskVisible')) ? localState.maskVisible : true;
        child.visible = parent.visible && localState.visible && maskVisible;
        return this;
    },

    syncVisible() {
        if (this.syncChildrenEnable) {
            this.children.forEach(this.updateChildVisible, this);
        }
        return this;
    },

    resetChildVisibleState(child) {
        var localState = GetLocalState(child);
        if (localState.hasOwnProperty('maskVisible')) {
            delete localState.maskVisible;
        }
        localState.visible = child.visible;
        return this;
    },

    setChildVisible(child, visible) {
        this.setChildLocalVisible(child, visible);
        return this;
    },
    setChildLocalVisible(child, visible) {
        if (visible === undefined) {
            visible = true;
        }
        var localState = GetLocalState(child);
        localState.visible = visible;
        this.updateChildVisible(child);
        return this;
    },
    setChildMaskVisible(child, visible) {
        if (visible === undefined) {
            visible = true;
        }
        var localState = GetLocalState(child);
        localState.maskVisible = visible;
        this.updateChildVisible(child);
        return this;
    },

    resetLocalVisibleState() {
        var parent = GetLocalState(this).parent;
        if (parent) {
            parent.resetChildVisibleState(this);
        }
        return this;
    }
};
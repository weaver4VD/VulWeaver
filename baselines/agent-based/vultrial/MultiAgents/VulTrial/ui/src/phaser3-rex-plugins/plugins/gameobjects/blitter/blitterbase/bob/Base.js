import DataMethods from '../../../../utils/data/DataMethods.js'

class Base {
    constructor(parent, type) {
        this.type = type;

        this.data = undefined;

        this
            .setParent(parent)
            .reset()
            .setActive();

    }

    destroy() {
        if (this.parent) {
            this.parent.removeChild(this);
        }
    }

    setParent(parent) {
        this.parent = parent;
        return this;
    }

    setDisplayListDirty(displayListDirty) {
        if (displayListDirty && this.parent) {
            this.parent.displayListDirty = true;
        }
        return this;
    }

    get active() {
        return this._active;
    }

    set active(value) {
        this.setDisplayListDirty(this._active != value);
        this._active = value;
    }

    setActive(active) {
        if (active === undefined) {
            active = true;
        }
        this.active = active;
        return this;
    }

    modifyPorperties(o) {
        return this;
    }
    reset() {
        this.clearData();
    }
    onFree() {
        this.reset().setActive(false).setParent();
    }
}

Object.assign(
    Base.prototype,
    DataMethods
);

export default Base;
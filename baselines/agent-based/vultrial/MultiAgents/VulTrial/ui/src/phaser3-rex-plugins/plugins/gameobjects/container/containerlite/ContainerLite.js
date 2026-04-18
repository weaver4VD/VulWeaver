import Base from './Base.js';
import Methods from './Methods.js';
import { GetParent } from './GetParent.js';

class ContainerLite extends Base {
    constructor(scene, x, y, width, height, children) {
        if (Array.isArray(width)) {
            children = width;
            width = undefined;
            height = undefined;
        }
        super(scene, x, y, width, height);
        this.type = 'rexContainerLite';
        this.isRexContainerLite = true;
        this.syncChildrenEnable = true;

        this._active = true;
        this._mask = null;
        this._scrollFactorX = 1;
        this._scrollFactorY = 1;
        this.privateRenderLayer = undefined;

        if (children) {
            this.add(children);
        }
    }

    destroy(fromScene) {
        if (!this.scene || this.ignoreDestroy) {
            return;
        }

        this.syncChildrenEnable = false;
        super.destroy(fromScene);

        if (this.privateRenderLayer) {
            this.privateRenderLayer.list.length = 0;
            this.privateRenderLayer.destroy();
        }
    }

    resize(width, height) {
        this.setSize(width, height);
        return this;
    }

    get x() {
        return this._x;
    }

    set x(value) {
        if (this._x === value) {
            return;
        }
        this._x = value;

        this.syncPosition();
    }

    get y() {
        return this._y;
    }

    set y(value) {
        if (this._y === value) {
            return;
        }
        this._y = value;

        this.syncPosition();
    }
    get rotation() {
        return super.rotation;
    }

    set rotation(value) {
        if (this.rotation === value) {
            return;
        }
        super.rotation = value;

        this.syncPosition();
    }
    get scaleX() {
        return super.scaleX;
    }

    set scaleX(value) {
        if (this.scaleX === value) {
            return;
        }
        super.scaleX = value;

        this.syncPosition();
    }
    get scaleY() {
        return super.scaleY;
    }

    set scaleY(value) {
        if (this.scaleY === value) {
            return;
        }
        super.scaleY = value;

        this.syncPosition();
    }
    get scale() {
        return super.scale;
    }

    set scale(value) {
        if (this.scale === value) {
            return;
        }
        super.scale = value;

        this.syncPosition();
    }
    get visible() {
        return super.visible;
    }

    set visible(value) {
        if (super.visible === value) {
            return;
        }
        super.visible = value;

        this.syncVisible();
    }
    get alpha() {
        return super.alpha;
    }

    set alpha(value) {
        if (super.alpha === value) {
            return;
        }
        super.alpha = value;

        this.syncAlpha();
    }
    get active() {
        return this._active;
    }

    set active(value) {
        if (this._active === value) {
            return;
        }
        this._active = value;

        this.syncActive();
    }
    get mask() {
        return this._mask;
    }
    set mask(mask) {
        if (this._mask === mask) {
            return;
        }
        this._mask = mask;

        this.syncMask();
    }
    get scrollFactorX() {
        return this._scrollFactorX;
    }

    set scrollFactorX(value) {
        if (this._scrollFactorX === value) {
            return;
        }

        this._scrollFactorX = value;
        this.syncScrollFactor();
    }
    get scrollFactorY() {
        return this._scrollFactorY;
    }

    set scrollFactorY(value) {
        if (this._scrollFactorY === value) {
            return;
        }

        this._scrollFactorY = value;
        this.syncScrollFactor();
    }
    get list() {
        return this.children;
    }

    static GetParent(child) {
        return GetParent(child);
    }
    get parentContainer() {
        return this._parentContainer;
    }

    set parentContainer(value) {
        if (!this._parentContainer && !value) {
            this._parentContainer = value;
            return;
        }
        if (this.setParentContainerFlag) {
            this._parentContainer = value;
            return;
        }
        if (this._parentContainer && !value) {
            this.removeFromContainer();
            this._parentContainer = value;
        } else if (value) {
            this._parentContainer = value;
            this.addToContainer(value);
        } else {
            this._parentContainer = value;
        }
    }

    get setParentContainerFlag() {
        if (this._setParentContainerFlag) {
            return true;
        }
        var parent = GetParent(this);
        return (parent) ? parent.setParentContainerFlag : false;
    }

}

Object.assign(
    ContainerLite.prototype,
    Methods
);

export default ContainerLite;
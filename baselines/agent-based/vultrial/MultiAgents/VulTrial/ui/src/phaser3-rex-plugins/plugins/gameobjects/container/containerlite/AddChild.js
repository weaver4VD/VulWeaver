import Base from './Base.js';
import GetLocalState from './utils/GetLocalState.js';

const GetValue = Phaser.Utils.Objects.GetValue;
const BaseAdd = Base.prototype.add;

var Add = function (gameObject, config) {
    this.setParent(gameObject);

    var state = GetLocalState(gameObject);
    SetupSyncFlags(state, config);

    this
        .resetChildState(gameObject)
        .updateChildVisible(gameObject)
        .updateChildActive(gameObject)
        .updateChildScrollFactor(gameObject)
        .updateChildMask(gameObject);

    BaseAdd.call(this, gameObject);

    this.addToParentContainer(gameObject);
    this.addToRenderLayer(gameObject);

    return this;
}

var AddLocal = function (gameObject, config) {
    this.setParent(gameObject);
    var state = GetLocalState(gameObject);
    SetupSyncFlags(state, config);
    state.x = gameObject.x;
    state.y = gameObject.y;
    state.rotation = gameObject.rotation;
    state.scaleX = gameObject.scaleX;
    state.scaleY = gameObject.scaleY;
    state.alpha = gameObject.alpha;
    state.visible = gameObject.visible;
    state.active = gameObject.active;

    this
        .updateChildPosition(gameObject)
        .updateChildAlpha(gameObject)
        .updateChildVisible(gameObject)
        .updateChildActive(gameObject)
        .updateChildScrollFactor(gameObject)
        .updateChildMask(gameObject);

    BaseAdd.call(this, gameObject);

    this.addToRenderLayer(gameObject);

    return this;
}

var SetupSyncFlags = function (state, config) {
    if (config === undefined) {
        config = true;
    }

    if (typeof (config) === 'boolean') {
        state.syncPosition = config;
        state.syncRotation = config;
        state.syncScale = config;
        state.syncAlpha = config;
        state.syncScrollFactor = config;
    } else {
        state.syncPosition = GetValue(config, 'syncPosition', true);
        state.syncRotation = GetValue(config, 'syncRotation', true);
        state.syncScale = GetValue(config, 'syncScale', true);
        state.syncAlpha = GetValue(config, 'syncAlpha', true);
        state.syncScrollFactor = GetValue(config, 'syncScrollFactor', true);
    }

}

export default {
    add(gameObject) {
        if (Array.isArray(gameObject)) {
            this.addMultiple(gameObject);
        } else {
            Add.call(this, gameObject);
        }
        return this;
    },
    pin(gameObject, config) {
        if (Array.isArray(gameObject)) {
            this.addMultiple(gameObject, config);
        } else {
            Add.call(this, gameObject, config);
        }
        return this;
    },

    addMultiple(gameObjects) {
        for (var i = 0, cnt = gameObjects.length; i < cnt; i++) {
            Add.call(this, gameObjects[i]);
        }
        return this;
    },

    addLocal(gameObject) {
        if (Array.isArray(gameObject)) {
            this.addMultiple(gameObject);
        } else {
            AddLocal.call(this, gameObject);
        }
        return this;
    },
    pinLocal(gameObject, config) {
        if (Array.isArray(gameObject)) {
            this.addMultiple(gameObject, config);
        } else {
            AddLocal.call(this, gameObject, config);
        }
        return this;
    },

    addLocalMultiple(gameObjects) {
        for (var i = 0, cnt = gameObjects.length; i < cnt; i++) {
            AddLocal.call(this, gameObjects[i]);
        }
        return this;
    }
};
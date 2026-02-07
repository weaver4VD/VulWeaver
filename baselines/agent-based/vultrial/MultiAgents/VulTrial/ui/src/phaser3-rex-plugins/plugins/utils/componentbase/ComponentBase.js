import EventEmitterMethods from '../eventemitter/EventEmitterMethods.js';
import GetSceneObject from '../system/GetSceneObject.js';
import GetGame from '../system/GetGame.js';

const GetValue = Phaser.Utils.Objects.GetValue;

class ComponentBase {
    constructor(parent, config) {
        this.setParent(parent);

        this.isShutdown = false;
        this.setEventEmitter(GetValue(config, 'eventEmitter', true));
        if (this.parent) {
            if (this.parent === this.scene) {
                this.scene.sys.events.once('shutdown', this.onEnvDestroy, this);

            } else if (this.parent === this.game) {
                this.game.events.once('shutdown', this.onEnvDestroy, this);

            } else if (this.parent.once) {
                this.parent.once('destroy', this.onParentDestroy, this);
            }
        }

    }

    shutdown(fromScene) {
        if (this.isShutdown) {
            return;
        }
        if (this.parent) {
            if (this.parent === this.scene) {
                this.scene.sys.events.off('shutdown', this.onEnvDestroy, this);

            } else if (this.parent === this.game) {
                this.game.events.off('shutdown', this.onEnvDestroy, this);

            } else if (this.parent.once) {
                this.parent.off('destroy', this.onParentDestroy, this);
            }
        }


        this.destroyEventEmitter();

        this.parent = undefined;
        this.scene = undefined;
        this.game = undefined;

        this.isShutdown = true;
    }

    destroy(fromScene) {
        this.shutdown(fromScene);
    }

    onEnvDestroy() {
        this.destroy(true);
    }

    onParentDestroy(parent, fromScene) {
        this.destroy(fromScene);
    }

    setParent(parent) {
        this.parent = parent;

        this.scene = GetSceneObject(parent);
        this.game = GetGame(parent);

        return this;
    }

};

Object.assign(
    ComponentBase.prototype,
    EventEmitterMethods
);

export default ComponentBase;
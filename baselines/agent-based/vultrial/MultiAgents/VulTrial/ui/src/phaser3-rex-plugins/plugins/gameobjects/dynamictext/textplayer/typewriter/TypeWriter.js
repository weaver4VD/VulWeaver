import EventEmitterMethods from '../../../../utils/eventemitter/EventEmitterMethods.js';
import Methods from './Methods.js';

const GetValue = Phaser.Utils.Objects.GetValue;

class TypeWriter {
    constructor(textPlayer, config) {
        this.setEventEmitter();
        this.textPlayer = textPlayer;
        this.isPageTyping = false;
        this.typingTimer = undefined;
        this.pauseTypingTimer = undefined;
        this.inTypingProcessLoop = false;
        this.isTypingPaused = false;
        this.setIgnoreWait(false);
        this.setSkipTypingAnimation(false);

        this.setTypingStartCallback(GetValue(config, 'onTypingStart', SetChildrenInvisible));
        this.setDefaultTypingSpeed(GetValue(config, 'speed', 250));
        this.setTypingSpeed();
        this.setSkipSpaceEnable(GetValue(config, 'skipSpace', false));
        this.setAnimationConfig(GetValue(config, 'animation', undefined));
        this.setMinSizeEnable(GetValue(config, 'minSizeEnable', false));

        this.setFadeOutPageCallback(GetValue(config, 'fadeOutPage'));

    }

    destroy() {
        this.destroyEventEmitter();

        this.textPlayer = undefined;

        this.typingTimer = undefined;

        this.pauseTypingTimer = undefined;

        this.onTypeStart = undefined;

        this.animationConfig = undefined;
    }

    get timeline() {
        return this.textPlayer.timeline;
    }

    setTypingStartCallback(callback) {
        this.onTypeStart = callback;
        return this;
    }

    setAnimationConfig(config) {
        if (!config) {
            config = {};
        }

        if (!config.hasOwnProperty('duration')) {
            config.duration = 0;
        }

        if (!config.hasOwnProperty('onStart')) {
            config.onStart = SetChildVisible;
        }

        this.animationConfig = config;
        return this;
    }

    setFadeOutPageCallback(callback) {
        this.fadeOutPageCallback = callback;
        return this;
    }

    setMinSizeEnable(enable) {
        if (enable === undefined) {
            enable = true;
        }

        this.minSizeEnable = enable;
        return this;
    }

    getNextChild() {
        var child = this.nextChild;
        this.index = Math.min(this.index + 1, this.children.length);
        this._nextChild = undefined;
        return child;
    }

    get nextChild() {
        if (!this._nextChild) {
            this._nextChild = this.children[this.index];
        }
        return this._nextChild;
    }
}

var SetChildVisible = function (child) {
    if (child.setVisible) {
        child.setVisible();
    }
}

var SetChildrenInvisible = function (children) {
    for (var i = 0, cnt = children.length; i < cnt; i++) {
        var child = children[i];
        if (child.setVisible) {
            child.setVisible(false);
        }
    }
}

Object.assign(
    TypeWriter.prototype,
    EventEmitterMethods,
    Methods,
);

export default TypeWriter;
import Label from '../label/Label.js';
import DefaultTransitCallbacks from './DefaultTransitCallbacks.js';
import Player from '../../../plugins/logic/runcommands/tcrp/Player.js';
import NOOP from '../../../plugins/utils/object/NOOP.js';

const GetValue = Phaser.Utils.Objects.GetValue;

class Toast extends Label {
    constructor(scene, config) {
        if (config === undefined) {
            config = {
                text: createDefaultTextObject(scene)
            }
        }

        super(scene, config);
        this.type = 'rexToast';

        this.setTransitInTime(GetValue(config, 'duration.in', 200));
        this.setDisplayTime(GetValue(config, 'duration.hold', 1200));
        this.setTransitOutTime(GetValue(config, 'duration.out', 200));
        this.setTransitInCallback(GetValue(config, 'transitIn', TransitionMode.popUp));
        this.setTransitOutCallback(GetValue(config, 'transitOut', TransitionMode.scaleDown));

        this.player = new Player(this, { dtMode: 1 });
        this.messages = [];
        this.scaleX0 = undefined;
        this.scaleY0 = undefined;

        this.setVisible(false);
    }

    destroy(fromScene) {
        if (!this.scene || this.ignoreDestroy) {
            return;
        }

        this.player.destroy();
        this.player = undefined;
        this.messages = undefined;

        super.destroy(fromScene);
    }

    setDisplayTime(time) {
        this.displayTime = time;
        return this;
    }

    setTransitOutTime(time) {
        this.transitOutTime = time;
        return this;
    }

    setTransitInTime(time) {
        this.transitInTime = time;
        return this;
    }

    setTransitInCallback(callback) {
        if (typeof (callback) === 'string') {
            callback = TransitionMode[callback];
        }

        switch (callback) {
            case TransitionMode.popUp:
                callback = DefaultTransitCallbacks.popUp;
                break;
            case TransitionMode.fadeIn:
                callback = DefaultTransitCallbacks.fadeIn;
                break;
        }

        if (!callback) {
            callback = NOOP;
        }

        this.transitInCallback = callback;
        return this;
    }

    setTransitOutCallback(callback) {
        if (typeof (callback) === 'string') {
            callback = TransitionMode[callback];
        }

        switch (callback) {
            case TransitionMode.scaleDown:
                callback = DefaultTransitCallbacks.scaleDown;
                break;
            case TransitionMode.fadeOut:
                callback = DefaultTransitCallbacks.fadeOut;
                break;
        }

        if (!callback) {
            callback = NOOP;
        }

        this.transitOutCallback = callback;
        return this;
    }

    setScale(scaleX, scaleY) {
        if (scaleY === undefined) {
            scaleY = scaleX;
        }
        this.scaleX0 = scaleX;
        this.scaleY0 = scaleY;

        super.setScale(scaleX, scaleY);
        return this;
    }

    showMessage(callback) {
        if (this.scaleX0 === undefined) {
            this.scaleX0 = this.scaleX;
        }
        if (this.scaleY0 === undefined) {
            this.scaleY0 = this.scaleY;
        }

        if (callback === undefined) {
            if (this.messages.length === 0) {
                return this;
            }
            callback = this.messages.shift();
        }

        if (this.player.isPlaying) {
            this.messages.push(callback);
            return this;
        }
        this
            .setScale(this.scaleX0, this.scaleY0)
            .setVisible(true);
        if (typeof (callback) === 'string') {
            this.setText(callback);
        } else {
            callback(this);
        }
        this.layout();

        var commands = [
            [
                0,
                [this.transitInCallback, this, this.transitInTime]
            ],
            [
                this.transitInTime,
                [NOOP]
            ],
            [
                this.displayTime,
                [this.transitOutCallback, this, this.transitOutTime]
            ],
            [
                this.transitOutTime,
                [this.setVisible, false]
            ],
            [
                30,
                [NOOP]
            ]
        ]
        this.player
            .load(commands, this)
            .once('complete', function () {
                this.showMessage();
            }, this)
            .start();

        return this;
    }
}

const TransitionMode = {
    popUp: 0,
    fadeIn: 1,
    scaleDown: 0,
    fadeOut: 1,
}

export default Toast;
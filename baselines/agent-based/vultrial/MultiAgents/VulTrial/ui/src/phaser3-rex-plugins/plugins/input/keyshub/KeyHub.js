import KeyMap from '../../utils/input/KeyMap.js';

const Key = Phaser.Input.Keyboard.Key;
const AddItem = Phaser.Utils.Array.Add;
const RemoveItem = Phaser.Utils.Array.Remove;

class KeyHub extends Key {
    constructor(parent, keyCode) {
        super(parent, keyCode);

        this.ports = [];
    }

    destroy() {
        for (var i = 0, cnt = this.ports.length; i < cnt; i++) {
            this.ports[i]
                .off('down', this.update, this)
                .off('up', this.update, this)
        }
        this.ports = undefined;
        super.destroy();
    }

    plug(key) {
        AddItem(this.ports, key, 0, function (key) {
            key
                .on('down', this.update, this)
                .on('up', this.update, this)

            this.update(FakeEvent);
        }, this);
        return this;
    }

    unplug(key) {
        RemoveItem(this.ports, key, function (key) {
            key
                .off('down', this.update, this)
                .off('up', this.update, this)

            this.update(FakeEvent);
        }, this);
        return this;
    }

    update(event) {
        if (event.cancelled === undefined) {
            event.cancelled = 0;
            event.stopImmediatePropagation = function () {
                event.cancelled = 1;
            };
            event.stopPropagation = function () {
                event.cancelled = -1;
            };
        }

        if (event.cancelled === -1) {
            event.cancelled = 0;
            return;
        }

        var isDown = false;
        for (var i = 0, cnt = this.ports.length; i < cnt; i++) {
            if (this.ports[i].isDown) {
                isDown = true;
                break;
            }
        }

        if (this.isDown !== isDown) {
            event = FakeEvent;
            event.timeStamp = Date.now();
            event.keyCode = this.keyCode;

            if (isDown) {
                this.onDown(event);
            } else {
                this.onUp(event);
            }

            if (!event.cancelled) {
                var eventName = ((isDown) ? 'keydown-' : 'keyup-') + KeyMap[this.keyCode];
                this.plugin.emit(eventName, event);
            }

            if (!event.cancelled) {
                var eventName = (isDown) ? 'keydown' : 'keyup';
                this.plugin.emit(eventName, event);
            }
        }

        event.cancelled = 0;
    }
}

var FakeEvent = {
    timeStamp: 0,
    keyCode: 0,
    altKey: false,
    ctrlKey: false,
    shiftKey: false,
    metaKey: false,
    location: 0,
};

export default KeyHub;
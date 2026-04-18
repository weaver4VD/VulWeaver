var MenuSetInteractive = function (menu) {
    menu
        .on(menu.root.expandEventName, function (button, index) {
            if (this._isPassedEvent) {
                return;
            }
            var childrenKey =  this.root.childrenKey;
            var subItems = this.items[index][childrenKey];
            if (subItems) {
                this.expandSubMenu(button, subItems);
            } else {
            }
        }, menu)
        .on('button.click', function (button, index, pointer, event) {
            if (this !== this.root) {
                this.root._isPassedEvent = true;
                this.root.emit('button.click', button, index, pointer, event);
                this.root._isPassedEvent = false;
            }
        }, menu)
        .on('button.over', function (button, index, pointer, event) {
            if (this !== this.root) {
                this.root._isPassedEvent = true;
                this.root.emit('button.over', button, index, pointer, event);
                this.root._isPassedEvent = false;
            }
        }, menu)
        .on('button.out', function (button, index, pointer, event) {
            if (this !== this.root) {
                this.root._isPassedEvent = true;
                this.root.emit('button.out', button, index, pointer, event);
                this.root._isPassedEvent = false;
            }
        }, menu);
};

export default MenuSetInteractive;
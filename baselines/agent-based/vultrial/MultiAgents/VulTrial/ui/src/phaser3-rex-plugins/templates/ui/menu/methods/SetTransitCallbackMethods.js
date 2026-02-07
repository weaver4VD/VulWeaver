import GetEaseConfig from './GetEaseConfig.js';

var PopUp = function (menu, duration) {
    menu.popUp(GetEaseConfig(menu.root.easeIn, menu))
}

var ScaleDown = function (menu, duration) {
    menu.scaleDown(GetEaseConfig(menu.root.easeOut, menu));
}

export default {
    setTransitInCallback(callback) {
        if (callback === undefined) {
            callback = PopUp;
        }

        this.transitInCallback = callback;
        return this;
    },

    setTransitOutCallback(callback) {
        if (callback === undefined) {
            callback = ScaleDown;
        }

        this.transitOutCallback = callback;
        return this;
    }
}
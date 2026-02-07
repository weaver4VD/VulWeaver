import ModalBehavior from './Modal.js';

var Modal = function (gameObject, config) {
    var modalBehavior = new ModalBehavior(gameObject, config);
    modalBehavior.on('open', function () {
        gameObject.emit('modal.open', modalBehavior);
    })
    modalBehavior.on('close', function (closeEventData) {
        gameObject.emit('modal.close', closeEventData, modalBehavior);
    })
    gameObject.on('modal.requestClose', modalBehavior.requestClose, modalBehavior);
    

    return modalBehavior;
}

var ModalPromise = function (gameObject, config) {
    var modalBehavior = Modal(gameObject, config);
    return new Promise(function (resolve, reject) {
        modalBehavior.once('close', function (closeEventData) {
            resolve(closeEventData);
        });
    });
}

var ModalClose = function (gameObject, closeEventData) {
    gameObject.emit('modal.requestClose', closeEventData);
}

export { Modal, ModalPromise, ModalClose };
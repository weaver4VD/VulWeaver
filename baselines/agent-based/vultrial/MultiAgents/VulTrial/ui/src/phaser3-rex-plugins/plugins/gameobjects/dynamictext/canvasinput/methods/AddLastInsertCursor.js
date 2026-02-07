import AddChild from '../../dynamictext/methods/AddChild.js';

var AddLastInsertCursor = function (textObject) {
    var child = textObject.createCharChild('|');
    child.text = '';
    AddChild.call(textObject, child);

    return child;
}

export default AddLastInsertCursor;
const GetValue = Phaser.Utils.Objects.GetValue;

var RouteEvents = function (gameObject, element, elementEvents, config) {
    var preventDefault = GetValue(config, 'preventDefault', false);
    var preTest = GetValue(config, 'preTest');
    for (let elementEventName in elementEvents) {
        element.addEventListener(elementEventName, function (e) {
            if (!preTest || preTest(gameObject, elementEventName)) {
                gameObject.emit(elementEvents[elementEventName], gameObject, e);
            }

            if (preventDefault) {
                e.preventDefault();
            }
        });
    }
}

export default RouteEvents;
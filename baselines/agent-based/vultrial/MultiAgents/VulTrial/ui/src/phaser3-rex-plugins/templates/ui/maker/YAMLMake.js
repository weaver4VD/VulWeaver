import ParseYAML from './utils/ParseYAML.js';
import Make from './Make.js';

var YAMLMake = function (scene, data, view, styles, customBuilders) {
    data = ParseYAML(data);
    if (Array.isArray(data)) {
        data = data[data.length - 1];
    } else if (data.$root) {
        var defaultStyles = data;
        data = data.$root;
        delete defaultStyles.$root;

        if (styles === undefined) {
            styles = defaultStyles;
        } else {
            for (var key in defaultStyles) {
                if (!styles[key]) {
                    styles[key] = defaultStyles[key];
                }
            }
        }
    }

    styles = ParseYAML(styles);

    var gameObject = Make(scene, data, view, styles, customBuilders);

    return gameObject;
}

export default YAMLMake;
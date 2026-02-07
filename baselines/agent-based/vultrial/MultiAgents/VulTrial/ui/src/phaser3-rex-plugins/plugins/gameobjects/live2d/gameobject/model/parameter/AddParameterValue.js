const Capitalize = Phaser.Utils.String.UppercaseFirst;

var AddParameterValue = function (name, value) {
    var propertyName = `_idParam${Capitalize(name)}`;
    if (!this.hasOwnProperty(propertyName)) {
        this.registerParameter(name);
        if (!this.hasOwnProperty(propertyName)) {
            return this;
        }
    }

    this._addParamValues[name] += value;

    return this;
}

export default AddParameterValue;
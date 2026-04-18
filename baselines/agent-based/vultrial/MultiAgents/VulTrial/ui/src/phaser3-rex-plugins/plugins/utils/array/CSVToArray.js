function CSVToArray(strData, strDelimiter, convert, convertScope) {
    strDelimiter = (strDelimiter || ",");
    var objPattern = new RegExp(
        (
            "(\\" + strDelimiter + "|\\r?\\n|\\r|^)" +
            "(?:\"([^\"]*(?:\"\"[^\"]*)*)\"|" +
            "([^\"\\" + strDelimiter + "\\r\\n]*))"
        ),
        "gi"
    );
    var arrLastRow = [];
    var arrData = [
        arrLastRow
    ];
    var arrMatches = null;
    while (arrMatches = objPattern.exec(strData)) {
        var strMatchedDelimiter = arrMatches[1];
        if (
            strMatchedDelimiter.length &&
            (strMatchedDelimiter != strDelimiter)
        ) {
            arrLastRow = [];
            arrData.push(arrLastRow);
        }
        if (arrMatches[2]) {
            var strMatchedValue = arrMatches[2].replace(
                new RegExp("\"\"", "g"),
                "\""
            );
        } else {
            var strMatchedValue = arrMatches[3];
        }
        if (convert) {
            if (convertScope) {
                strMatchedValue = convert.call(convertScope, strMatchedValue);
            } else {
                strMatchedValue = convert(strMatchedValue);
            }
        }
        arrLastRow.push(strMatchedValue);
    }
    return (arrData);
};

export default CSVToArray;
const VERSION = '7.19.0';

var GetDefaultUrl = function (version) {
    if (version === undefined) {
        version = VERSION
    }
    return {
        app: `https://www.gstatic.com/firebasejs/${version}/firebase-app.js`,
        database: `https://www.gstatic.com/firebasejs/${version}/firebase-database.js`,
        firestore: `https://www.gstatic.com/firebasejs/${version}/firebase-firestore.js`,
    }
}

export default GetDefaultUrl;

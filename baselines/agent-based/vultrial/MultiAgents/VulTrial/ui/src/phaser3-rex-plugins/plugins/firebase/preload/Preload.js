import GetDefaultUrl from './GetDefaultUrl.js';
import MergeRight from '../../utils/object/MergeRight.js';
import LoadScriptPromise from '../../utils/loader/LoadScriptPromise.js';
import AvailableTest from './AvailableTest.js';

var Preload = function (urlConfig, firebaseConfig) {
    if (typeof (urlConfig) === 'string') {
        urlConfig = GetDefaultUrl(urlConfig);
    } else {
        urlConfig = MergeRight(GetDefaultUrl(), urlConfig);
    }

    return LoadScriptPromise(urlConfig.app)
        .then(function () {
            var promises = [];
            var url;
            for (var k in urlConfig) {
                if (k === 'app') {
                    continue;
                }
                url = urlConfig[k];
                if (!url) {
                    continue;
                }
                promises.push(LoadScriptPromise(url))
            }

            if (promises.length === 0) {
                return Promise.resolve();
            } else {
                return Promise.all(promises);
            }
        })
        .then(function () {
            return AvailableTest(urlConfig);
        })
        .then(function () {
            if (firebaseConfig !== undefined) {
                firebase.initializeApp(firebaseConfig);
            }
            return Promise.resolve();
        })
}

export default Preload;
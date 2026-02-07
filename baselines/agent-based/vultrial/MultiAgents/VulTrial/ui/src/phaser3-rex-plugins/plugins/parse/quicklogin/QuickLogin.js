var QuickLogin = function (userName, password) {
    return Parse.User.logOut()
        .then(function () {
            return Parse.User.logIn(userName, password);
        })
        .catch(function () {
            return SignUpThenLogin(userName, password);
        })
}

var SignUpThenLogin = function (userName, password) {
    var user = new Parse.User();
    user
        .set('username', userName)
        .set('password', password);

    return user.signUp()
        .then(function () {
            return Parse.User.logIn(userName, password);
        })
}

export default QuickLogin;
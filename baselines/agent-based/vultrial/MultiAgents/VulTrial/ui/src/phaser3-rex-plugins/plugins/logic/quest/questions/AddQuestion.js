var AddQuestion = function (question) {
    Polyfills.call(this, question);
    var key = question.key;
    if (this.questionMap.hasOwnProperty(key)) {
        this.remove(key);
    }
    this.questions.push(question);
    this.questionMap[key] = question;

    return this;
}

var Polyfills = function (question) {
    var options = question.options;
    if (options) {
        for (var i = 0, cnt = options.length; i < cnt; i++) {
            var option = options[i];
            if (!option.hasOwnProperty('key')) {
                option.key = `_${i}`;
            }
        }
    }

    if (!question.hasOwnProperty('key')) {
        question.key = `_${this.questions.length}`;
    }
}

export default AddQuestion;

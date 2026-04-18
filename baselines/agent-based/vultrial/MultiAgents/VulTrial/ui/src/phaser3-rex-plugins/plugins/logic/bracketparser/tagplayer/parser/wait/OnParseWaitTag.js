var OnParseWaitTag = function (tagPlayer, parser, config) {
    var tagWait = 'wait';
    var tagClick = 'click';
    parser
        .on(`+${tagWait}`, function (name) {
            tagPlayer.wait(name);
            parser.skipEvent();
        })
        .on(`-${tagWait}`, function () {
            parser.skipEvent();
        })
        .on(`+${tagClick}`, function () {
            tagPlayer.wait('click');
            parser.skipEvent();
        })
        .on(`-${tagClick}`, function () {
            parser.skipEvent();
        })
}

export default OnParseWaitTag;
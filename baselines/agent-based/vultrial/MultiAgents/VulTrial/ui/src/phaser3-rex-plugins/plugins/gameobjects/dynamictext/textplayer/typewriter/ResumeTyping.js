var ResumeTyping = function (offsetTime) {
    if (!this.isTypingPaused) {
        return this;
    }
    if (offsetTime === undefined) {
        offsetTime = 0;
    }

    if (this.typingTimer) {
        this.isTypingPaused = false;
        this.typingTimer.resume();
        this.typingTimer.remainder += offsetTime;
    } else if (this.isTypingPaused) {
        this.isTypingPaused = false;
        this.typing(offsetTime);
    }
    return this;
}

export default ResumeTyping;
var PauseTyping = function () {
    if (this.isTypingPaused) {
        return this;
    }

    if (this.typingTimer) {
        this.typingTimer.pause();
        this.isTypingPaused = true;
    } else if (this.inTypingProcessLoop) {
        this.inTypingProcessLoop = false;
        this.isTypingPaused = true;
    }
    return this;
}

export default PauseTyping;
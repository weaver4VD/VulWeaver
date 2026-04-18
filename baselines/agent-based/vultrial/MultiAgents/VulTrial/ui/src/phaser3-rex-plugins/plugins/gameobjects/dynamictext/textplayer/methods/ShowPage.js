var ShowPage = function () {
    if (!this.isPlaying || !this.isPageTyping) {
        return this;
    }
    var typingSpeedSave = this.typeWriter.speed;
    var ignoreWaitSave = this.typeWriter.ignoreWait;
    var skipTypingAnimationSave = this.typeWriter.skipTypingAnimation;
    var skipSoundEffectSave = this.typeWriter.skipSoundEffect;

    this.typeWriter
        .once('complete', function () {
            this.typeWriter
                .setTypingSpeed(typingSpeedSave)
                .setIgnoreWait(ignoreWaitSave)
                .setSkipTypingAnimation(skipTypingAnimationSave)
                .setSkipSoundEffect(skipSoundEffectSave)

        }, this)

        .setTypingSpeed(0)
        .skipCurrentTypingDelay()
        .setIgnoreWait(true)
        .setSkipTypingAnimation(true)
        .setSkipSoundEffect(true)

    return this;
}

export default ShowPage;
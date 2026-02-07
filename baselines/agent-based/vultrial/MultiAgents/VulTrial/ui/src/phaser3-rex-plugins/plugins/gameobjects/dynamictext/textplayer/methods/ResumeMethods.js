export default {
    resume() {
        this.timeline.resume();

        return this;
    },

    resumeTyping(offsetTime) {
        this.typeWriter.resumeTyping(offsetTime);

        return this;
    }
}
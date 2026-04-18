export default {
    pause() {
        this.timeline.pause(); 

        return this;
    },

    pauseTyping() {
        this.typeWriter.pauseTyping();

        return this;
    }
};
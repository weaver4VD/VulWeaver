const FadeMode = {
    tint: 0,
    alpha: 1
}

export default {
    setGOFadeMode(fadeMode) {
        if (typeof (fadeMode) === 'string') {
            fadeMode = FadeMode[fadeMode];
        }

        this.fadeMode = fadeMode;
        return this;
    },

    setGOFadeTime(time) {
        this.fadeTime = time;
        return this;
    },

    hasTintFadeEffect(gameObject) {
        return ((this.fadeMode === undefined) || (this.fadeMode === 0)) &&
            (this.fadeTime > 0) && (gameObject.setTint !== undefined);
    },

    hasAlphaFadeEffect(gameObject) {
        return ((this.fadeMode === undefined) || (this.fadeMode === 1)) &&
            (this.fadeTime > 0) && (gameObject.setAlpha !== undefined);
    },

    fadeBob(bob, fromValue, toValue, onComplete) {
        var gameObject = bob.gameObject;
        if (this.hasTintFadeEffect(gameObject)) {
            if (fromValue !== undefined) {
                bob.setProperty('tintGray', 255 * fromValue)
            }
            bob.easeProperty(
                'tintGray',
                Math.floor(255 * toValue),
                this.fadeTime,
                'Linear',
                0,
                false,
                onComplete
            )

        } else if (this.hasAlphaFadeEffect(gameObject)) {
            if (fromValue !== undefined) {
                bob.setProperty('alpha', fromValue);
            }
            bob.easeProperty(
                'alpha',
                toValue,
                this.fadeTime,
                'Linear',
                0,
                false,
                onComplete
            )
        } else {
            if (onComplete) {
                onComplete(gameObject);
            }
        }

        return this;
    }

}
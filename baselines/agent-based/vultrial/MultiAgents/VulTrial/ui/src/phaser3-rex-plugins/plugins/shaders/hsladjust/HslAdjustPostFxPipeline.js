import FragSrc from './hslAdjust-postfxfrag.js';

const PostFXPipeline = Phaser.Renderer.WebGL.Pipelines.PostFXPipeline;
const GetValue = Phaser.Utils.Objects.GetValue;

class HslAdjustPostFxPipeline extends PostFXPipeline {
    constructor(game) {
        super({
            name: 'rexHslAdjustPostFx',
            game: game,
            renderTarget: true,
            fragShader: FragSrc
        });

        this.hueRotate = 0;
        this.satAdjust = 1;
        this.lumAdjust = 0.5;
    }

    resetFromJSON(o) {
        this.setHueRotate(GetValue(o, 'hueRotate', 0));
        this.setSatAdjust(GetValue(o, 'satAdjust', 1));
        this.setLumAdjust(GetValue(o, 'lumAdjust', 0.5));
        return this;
    }

    onPreRender() {
        this.set1f('hueRotate', (this.hueRotate) % 1);
        this.set1f('satAdjust', this.satAdjust);
        this.set1f('lumAdjust', this.lumAdjust);
    }
    setHueRotate(value) {
        this.hueRotate = value;
        return this;
    }
    setSatAdjust(value) {
        this.satAdjust = value;
        return this;
    }
    setLumAdjust(value) {
        this.lumAdjust = value;
        return this;
    }
}

export default HslAdjustPostFxPipeline;
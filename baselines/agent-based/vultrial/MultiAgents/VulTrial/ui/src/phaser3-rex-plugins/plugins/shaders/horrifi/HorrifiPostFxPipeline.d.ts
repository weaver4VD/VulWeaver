export default HorrifiPostFxPipeline;

declare namespace HorrifiPostFxPipeline {
    interface IConfig {
        enable?: boolean,
        bloomEnable?: boolean,
        bloomRadius?: number, bloomIntensity?: number, bloomThreshold?: number,
        bloomTexelWidth?: number, bloomTexelHeight?: number,
        chromaticEnable?: boolean,
        chabIntensity?: number,
        vignetteEnable?: boolean,
        vignetteStrength?: number, vignetteIntensity?: number,
        noiseEnable?: boolean,
        noiseStrength?: number,
        noiseSeed?: number,
        vhsEnable?: boolean,
        vhsStrength?: number,
        scanlinesEnable?: boolean,
        scanStrength?: number,
        crtEnable?: boolean,
        crtWidth?: number, crtHeight?: number,

    }
}

declare class HorrifiPostFxPipeline extends Phaser.Renderer.WebGL.Pipelines.PostFXPipeline {
    bloomEnable: boolean;
    bloomRadius: number;
    bloomIntensity: number;
    bloomThreshold: number;
    bloomTexelWidth: number;
    bloomTexelHeight: number;
    chromaticEnable: boolean;
    chabIntensity: number;
    vignetteEnable: boolean;
    vignetteStrength: number;
    vignetteIntensity: number;
    noiseEnable: boolean;
    noiseStrength: number;
    noiseSeed: number;
    vhsEnable: boolean;
    vhsStrength: number;
    scanlinesEnable: boolean;
    scanStrength: number;
    crtEnable: boolean;
    crtWidth: number;
    crtHeight: number;
    setBloomEnable(enable?: boolean): this;
    setBloomRadius(value: number): this;
    setBloomIntensity(value: number): this;
    setBloomThreshold(value: number): this;
    setBloomTexelSize(width: number, height?: number): this;
    setChromaticEnable(enable?: boolean): this;
    setChabIntensity(value: number): this;
    setVignetteEnable(Genable?: boolean): this;
    setVignetteStrength(value: number): this;
    setVignetteIntensity(value: number): this;
    setNoiseEnable(enable?: boolean): this;
    setNoiseStrength(value: number): this;
    setNoiseSeed(value: number): this;
    setVHSEnable(enable?: boolean): this;
    setVhsStrength(value: number): this;
    setScanlinesEnable(enable?: boolean): this;
    setScanStrength(value: number): this;
    setCRTEnable(enable?: boolean): this;
    setCrtSize(width: number, height?: number): this;

}
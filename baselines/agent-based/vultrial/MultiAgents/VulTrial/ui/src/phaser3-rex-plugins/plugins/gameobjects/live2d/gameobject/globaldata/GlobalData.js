import GetGame from '../../../../utils/system/GetGame.js';
import CanvasMatrix from './CanvasMatrix.js';

var GlobalDataInstance = undefined;
class GlobalData {
    static getInstance(gameObject) {
        if (!GlobalDataInstance) {
            GlobalDataInstance = new GlobalData(gameObject);
        }
        return GlobalDataInstance;
    }

    constructor(gameObject) {
        var game = GetGame(gameObject);
        var gl = game.renderer.gl;
        var scale = game.scale;

        this.game = game;
        this.gl = gl;
        this.scale = scale;
        this.frameBuffer = gl.getParameter(gl.FRAMEBUFFER_BINDING);

        this.viewportRect = [0, 0, 0, 0];
        this.projectionMatrix = new CanvasMatrix();
        this.onResize();

        scale.on('resize', this.onResize, this);
        game.events.once('destroy', this.destroy, this);
    }

    destroy() {
        this.scale.off('resize', this.onResize, this);

        this.game = undefined;
        this.gl = undefined;
        this.scale = undefined;

        this.frameBuffer = undefined;
        this.viewportRect = undefined;
        this.projectionMatrix = undefined;

        GlobalDataInstance = undefined;
    }

    get canvasWidth() {
        return this.scale.width;
    }

    get canvasHeight() {
        return this.scale.height;
    }

    onResize() {
        var width = this.canvasWidth;
        var height = this.canvasHeight;
        this.viewportRect[2] = width;
        this.viewportRect[3] = height;
        this.projectionMatrix.setSize(width, height);
    }
}

export default GlobalData;


import { Constant } from '../live2dcubismframework';
import { CubismMatrix44 } from '../math/cubismmatrix44';
import { CubismModel } from '../model/cubismmodel';
import { csmMap } from '../type/csmmap';
import { csmRect } from '../type/csmrectf';
import { csmVector } from '../type/csmvector';
import { CubismLogError } from '../utils/cubismdebug';
import {
  CubismBlendMode,
  CubismRenderer,
  CubismTextureColor
} from './cubismrenderer';

const ColorChannelCount = 4;

const shaderCount = 10;
let s_instance: CubismShader_WebGL;
let s_viewport: number[];
let s_fbo: WebGLFramebuffer;


export class CubismClippingManager_WebGL {
  
  public getChannelFlagAsColor(channelNo: number): CubismTextureColor {
    return this._channelColors.at(channelNo);
  }

  
  public getMaskRenderTexture(): WebGLFramebuffer {
    let ret: WebGLFramebuffer = 0;
    if (this._maskTexture && this._maskTexture.texture != 0) {
      this._maskTexture.frameNo = this._currentFrameNo;
      ret = this._maskTexture.texture;
    }

    if (ret == 0) {
      const size: number = this._clippingMaskBufferSize;

      this._colorBuffer = this.gl.createTexture();
      this.gl.bindTexture(this.gl.TEXTURE_2D, this._colorBuffer);
      this.gl.texImage2D(
        this.gl.TEXTURE_2D,
        0,
        this.gl.RGBA,
        size,
        size,
        0,
        this.gl.RGBA,
        this.gl.UNSIGNED_BYTE,
        null
      );
      this.gl.texParameteri(
        this.gl.TEXTURE_2D,
        this.gl.TEXTURE_WRAP_S,
        this.gl.CLAMP_TO_EDGE
      );
      this.gl.texParameteri(
        this.gl.TEXTURE_2D,
        this.gl.TEXTURE_WRAP_T,
        this.gl.CLAMP_TO_EDGE
      );
      this.gl.texParameteri(
        this.gl.TEXTURE_2D,
        this.gl.TEXTURE_MIN_FILTER,
        this.gl.LINEAR
      );
      this.gl.texParameteri(
        this.gl.TEXTURE_2D,
        this.gl.TEXTURE_MAG_FILTER,
        this.gl.LINEAR
      );
      this.gl.bindTexture(this.gl.TEXTURE_2D, null);

      ret = this.gl.createFramebuffer();
      this.gl.bindFramebuffer(this.gl.FRAMEBUFFER, ret);
      this.gl.framebufferTexture2D(
        this.gl.FRAMEBUFFER,
        this.gl.COLOR_ATTACHMENT0,
        this.gl.TEXTURE_2D,
        this._colorBuffer,
        0
      );
      this.gl.bindFramebuffer(this.gl.FRAMEBUFFER, s_fbo);

      this._maskTexture = new CubismRenderTextureResource(
        this._currentFrameNo,
        ret
      );
    }

    return ret;
  }

  
  public setGL(gl: WebGLRenderingContext): void {
    this.gl = gl;
  }

  
  public calcClippedDrawTotalBounds(
    model: CubismModel,
    clippingContext: CubismClippingContext
  ): void {
    let clippedDrawTotalMinX: number = Number.MAX_VALUE;
    let clippedDrawTotalMinY: number = Number.MAX_VALUE;
    let clippedDrawTotalMaxX: number = Number.MIN_VALUE;
    let clippedDrawTotalMaxY: number = Number.MIN_VALUE;
    const clippedDrawCount: number =
      clippingContext._clippedDrawableIndexList.length;

    for (
      let clippedDrawableIndex = 0;
      clippedDrawableIndex < clippedDrawCount;
      clippedDrawableIndex++
    ) {
      const drawableIndex: number =
        clippingContext._clippedDrawableIndexList[clippedDrawableIndex];

      const drawableVertexCount: number = model.getDrawableVertexCount(
        drawableIndex
      );
      const drawableVertexes: Float32Array = model.getDrawableVertices(
        drawableIndex
      );

      let minX: number = Number.MAX_VALUE;
      let minY: number = Number.MAX_VALUE;
      let maxX: number = Number.MIN_VALUE;
      let maxY: number = Number.MIN_VALUE;

      const loop: number = drawableVertexCount * Constant.vertexStep;
      for (
        let pi: number = Constant.vertexOffset;
        pi < loop;
        pi += Constant.vertexStep
      ) {
        const x: number = drawableVertexes[pi];
        const y: number = drawableVertexes[pi + 1];

        if (x < minX) {
          minX = x;
        }
        if (x > maxX) {
          maxX = x;
        }
        if (y < minY) {
          minY = y;
        }
        if (y > maxY) {
          maxY = y;
        }
      }
      if (minX == Number.MAX_VALUE) {
        continue;
      }
      if (minX < clippedDrawTotalMinX) {
        clippedDrawTotalMinX = minX;
      }
      if (minY < clippedDrawTotalMinY) {
        clippedDrawTotalMinY = minY;
      }
      if (maxX > clippedDrawTotalMaxX) {
        clippedDrawTotalMaxX = maxX;
      }
      if (maxY > clippedDrawTotalMaxY) {
        clippedDrawTotalMaxY = maxY;
      }

      if (clippedDrawTotalMinX == Number.MAX_VALUE) {
        clippingContext._allClippedDrawRect.x = 0.0;
        clippingContext._allClippedDrawRect.y = 0.0;
        clippingContext._allClippedDrawRect.width = 0.0;
        clippingContext._allClippedDrawRect.height = 0.0;
        clippingContext._isUsing = false;
      } else {
        clippingContext._isUsing = true;
        const w: number = clippedDrawTotalMaxX - clippedDrawTotalMinX;
        const h: number = clippedDrawTotalMaxY - clippedDrawTotalMinY;
        clippingContext._allClippedDrawRect.x = clippedDrawTotalMinX;
        clippingContext._allClippedDrawRect.y = clippedDrawTotalMinY;
        clippingContext._allClippedDrawRect.width = w;
        clippingContext._allClippedDrawRect.height = h;
      }
    }
  }

  
  public constructor() {
    this._maskRenderTexture = null;
    this._colorBuffer = null;
    this._currentFrameNo = 0;
    this._clippingMaskBufferSize = 256;
    this._clippingContextListForMask = new csmVector<CubismClippingContext>();
    this._clippingContextListForDraw = new csmVector<CubismClippingContext>();
    this._channelColors = new csmVector<CubismTextureColor>();
    this._tmpBoundsOnModel = new csmRect();
    this._tmpMatrix = new CubismMatrix44();
    this._tmpMatrixForMask = new CubismMatrix44();
    this._tmpMatrixForDraw = new CubismMatrix44();
    this._maskTexture = null;

    let tmp: CubismTextureColor = new CubismTextureColor();
    tmp.R = 1.0;
    tmp.G = 0.0;
    tmp.B = 0.0;
    tmp.A = 0.0;
    this._channelColors.pushBack(tmp);

    tmp = new CubismTextureColor();
    tmp.R = 0.0;
    tmp.G = 1.0;
    tmp.B = 0.0;
    tmp.A = 0.0;
    this._channelColors.pushBack(tmp);

    tmp = new CubismTextureColor();
    tmp.R = 0.0;
    tmp.G = 0.0;
    tmp.B = 1.0;
    tmp.A = 0.0;
    this._channelColors.pushBack(tmp);

    tmp = new CubismTextureColor();
    tmp.R = 0.0;
    tmp.G = 0.0;
    tmp.B = 0.0;
    tmp.A = 1.0;
    this._channelColors.pushBack(tmp);
  }

  
  public release(): void {
    for (let i = 0; i < this._clippingContextListForMask.getSize(); i++) {
      if (this._clippingContextListForMask.at(i)) {
        this._clippingContextListForMask.at(i).release();
        this._clippingContextListForMask.set(i, void 0);
      }
      this._clippingContextListForMask.set(i, null);
    }
    this._clippingContextListForMask = null;
    for (let i = 0; i < this._clippingContextListForDraw.getSize(); i++) {
      this._clippingContextListForDraw.set(i, null);
    }
    this._clippingContextListForDraw = null;

    if (this._maskTexture) {
      this.gl.deleteFramebuffer(this._maskTexture.texture);
      this._maskTexture = null;
    }

    for (let i = 0; i < this._channelColors.getSize(); i++) {
      this._channelColors.set(i, null);
    }

    this._channelColors = null;
    this.gl.deleteTexture(this._colorBuffer);
    this._colorBuffer = null;
  }

  
  public initialize(
    model: CubismModel,
    drawableCount: number,
    drawableMasks: Int32Array[],
    drawableMaskCounts: Int32Array
  ): void {
    for (let i = 0; i < drawableCount; i++) {
      if (drawableMaskCounts[i] <= 0) {
        this._clippingContextListForDraw.pushBack(null);
        continue;
      }
      let clippingContext: CubismClippingContext = this.findSameClip(
        drawableMasks[i],
        drawableMaskCounts[i]
      );
      if (clippingContext == null) {
        clippingContext = new CubismClippingContext(
          this,
          drawableMasks[i],
          drawableMaskCounts[i]
        );
        this._clippingContextListForMask.pushBack(clippingContext);
      }

      clippingContext.addClippedDrawable(i);

      this._clippingContextListForDraw.pushBack(clippingContext);
    }
  }

  
  public setupClippingContext(
    model: CubismModel,
    renderer: CubismRenderer_WebGL
  ): void {
    this._currentFrameNo++;
    let usingClipCount = 0;
    for (
      let clipIndex = 0;
      clipIndex < this._clippingContextListForMask.getSize();
      clipIndex++
    ) {
      const cc: CubismClippingContext = this._clippingContextListForMask.at(
        clipIndex
      );
      this.calcClippedDrawTotalBounds(model, cc);

      if (cc._isUsing) {
        usingClipCount++;
      }
    }
    if (usingClipCount > 0) {
      this.gl.viewport(
        0,
        0,
        this._clippingMaskBufferSize,
        this._clippingMaskBufferSize
      );
      this._maskRenderTexture = this.getMaskRenderTexture();
      const modelToWorldF: CubismMatrix44 = renderer.getMvpMatrix();

      renderer.preDraw();
      this.setupLayoutBounds(usingClipCount);
      this.gl.bindFramebuffer(this.gl.FRAMEBUFFER, this._maskRenderTexture);
      this.gl.clearColor(1.0, 1.0, 1.0, 1.0);
      this.gl.clear(this.gl.COLOR_BUFFER_BIT);
      for (
        let clipIndex = 0;
        clipIndex < this._clippingContextListForMask.getSize();
        clipIndex++
      ) {
        const clipContext: CubismClippingContext = this._clippingContextListForMask.at(
          clipIndex
        );
        const allClipedDrawRect: csmRect = clipContext._allClippedDrawRect;
        const layoutBoundsOnTex01: csmRect = clipContext._layoutBounds;
        const MARGIN = 0.05;
        this._tmpBoundsOnModel.setRect(allClipedDrawRect);
        this._tmpBoundsOnModel.expand(
          allClipedDrawRect.width * MARGIN,
          allClipedDrawRect.height * MARGIN
        );
        const scaleX: number =
          layoutBoundsOnTex01.width / this._tmpBoundsOnModel.width;
        const scaleY: number =
          layoutBoundsOnTex01.height / this._tmpBoundsOnModel.height;
        {
          this._tmpMatrix.loadIdentity();
          {
            this._tmpMatrix.translateRelative(-1.0, -1.0);
            this._tmpMatrix.scaleRelative(2.0, 2.0);
          }
          {
            this._tmpMatrix.translateRelative(
              layoutBoundsOnTex01.x,
              layoutBoundsOnTex01.y
            );
            this._tmpMatrix.scaleRelative(scaleX, scaleY);
            this._tmpMatrix.translateRelative(
              -this._tmpBoundsOnModel.x,
              -this._tmpBoundsOnModel.y
            );
          }
          this._tmpMatrixForMask.setMatrix(this._tmpMatrix.getArray());
        }
        {
          this._tmpMatrix.loadIdentity();
          {
            this._tmpMatrix.translateRelative(
              layoutBoundsOnTex01.x,
              layoutBoundsOnTex01.y
            );
            this._tmpMatrix.scaleRelative(scaleX, scaleY);
            this._tmpMatrix.translateRelative(
              -this._tmpBoundsOnModel.x,
              -this._tmpBoundsOnModel.y
            );
          }
          this._tmpMatrixForDraw.setMatrix(this._tmpMatrix.getArray());
        }
        clipContext._matrixForMask.setMatrix(this._tmpMatrixForMask.getArray());
        clipContext._matrixForDraw.setMatrix(this._tmpMatrixForDraw.getArray());

        const clipDrawCount: number = clipContext._clippingIdCount;
        for (let i = 0; i < clipDrawCount; i++) {
          const clipDrawIndex: number = clipContext._clippingIdList[i];
          if (
            !model.getDrawableDynamicFlagVertexPositionsDidChange(clipDrawIndex)
          ) {
            continue;
          }

          renderer.setIsCulling(
            model.getDrawableCulling(clipDrawIndex) != false
          );
          renderer.setClippingContextBufferForMask(clipContext);
          renderer.drawMesh(
            model.getDrawableTextureIndices(clipDrawIndex),
            model.getDrawableVertexIndexCount(clipDrawIndex),
            model.getDrawableVertexCount(clipDrawIndex),
            model.getDrawableVertexIndices(clipDrawIndex),
            model.getDrawableVertices(clipDrawIndex),
            model.getDrawableVertexUvs(clipDrawIndex),
            model.getDrawableOpacity(clipDrawIndex),
            CubismBlendMode.CubismBlendMode_Normal,
            false
          );
        }
      }
      this.gl.bindFramebuffer(this.gl.FRAMEBUFFER, s_fbo);
      renderer.setClippingContextBufferForMask(null);

      this.gl.viewport(
        s_viewport[0],
        s_viewport[1],
        s_viewport[2],
        s_viewport[3]
      );
    }
  }

  
  public findSameClip(
    drawableMasks: Int32Array,
    drawableMaskCounts: number
  ): CubismClippingContext {
    for (let i = 0; i < this._clippingContextListForMask.getSize(); i++) {
      const clippingContext: CubismClippingContext = this._clippingContextListForMask.at(
        i
      );
      const count: number = clippingContext._clippingIdCount;
      if (count != drawableMaskCounts) {
        continue;
      }

      let sameCount = 0;
      for (let j = 0; j < count; j++) {
        const clipId: number = clippingContext._clippingIdList[j];

        for (let k = 0; k < count; k++) {
          if (drawableMasks[k] == clipId) {
            sameCount++;
            break;
          }
        }
      }

      if (sameCount == count) {
        return clippingContext;
      }
    }

    return null;
  }

  
  public setupLayoutBounds(usingClipCount: number): void {
    let div: number = usingClipCount / ColorChannelCount;
    let mod: number = usingClipCount % ColorChannelCount;
    div = ~~div;
    mod = ~~mod;
    let curClipIndex = 0;

    for (let channelNo = 0; channelNo < ColorChannelCount; channelNo++) {
      const layoutCount: number = div + (channelNo < mod ? 1 : 0);
      if (layoutCount == 0) {
      } else if (layoutCount == 1) {
        const clipContext: CubismClippingContext = this._clippingContextListForMask.at(
          curClipIndex++
        );
        clipContext._layoutChannelNo = channelNo;
        clipContext._layoutBounds.x = 0.0;
        clipContext._layoutBounds.y = 0.0;
        clipContext._layoutBounds.width = 1.0;
        clipContext._layoutBounds.height = 1.0;
      } else if (layoutCount == 2) {
        for (let i = 0; i < layoutCount; i++) {
          let xpos: number = i % 2;
          xpos = ~~xpos;

          const cc: CubismClippingContext = this._clippingContextListForMask.at(
            curClipIndex++
          );
          cc._layoutChannelNo = channelNo;

          cc._layoutBounds.x = xpos * 0.5;
          cc._layoutBounds.y = 0.0;
          cc._layoutBounds.width = 0.5;
          cc._layoutBounds.height = 1.0;
        }
      } else if (layoutCount <= 4) {
        for (let i = 0; i < layoutCount; i++) {
          let xpos: number = i % 2;
          let ypos: number = i / 2;
          xpos = ~~xpos;
          ypos = ~~ypos;

          const cc = this._clippingContextListForMask.at(curClipIndex++);
          cc._layoutChannelNo = channelNo;

          cc._layoutBounds.x = xpos * 0.5;
          cc._layoutBounds.y = ypos * 0.5;
          cc._layoutBounds.width = 0.5;
          cc._layoutBounds.height = 0.5;
        }
      } else if (layoutCount <= 9) {
        for (let i = 0; i < layoutCount; i++) {
          let xpos = i % 3;
          let ypos = i / 3;
          xpos = ~~xpos;
          ypos = ~~ypos;

          const cc: CubismClippingContext = this._clippingContextListForMask.at(
            curClipIndex++
          );
          cc._layoutChannelNo = channelNo;

          cc._layoutBounds.x = xpos / 3.0;
          cc._layoutBounds.y = ypos / 3.0;
          cc._layoutBounds.width = 1.0 / 3.0;
          cc._layoutBounds.height = 1.0 / 3.0;
        }
      } else {
        CubismLogError('not supported mask count : {0}', layoutCount);
      }
    }
  }

  
  public getColorBuffer(): WebGLTexture {
    return this._colorBuffer;
  }

  
  public getClippingContextListForDraw(): csmVector<CubismClippingContext> {
    return this._clippingContextListForDraw;
  }

  
  public setClippingMaskBufferSize(size: number): void {
    this._clippingMaskBufferSize = size;
  }

  
  public getClippingMaskBufferSize(): number {
    return this._clippingMaskBufferSize;
  }

  public _maskRenderTexture: WebGLFramebuffer;
  public _colorBuffer: WebGLTexture;
  public _currentFrameNo: number;

  public _channelColors: csmVector<CubismTextureColor>;
  public _maskTexture: CubismRenderTextureResource;
  public _clippingContextListForMask: csmVector<CubismClippingContext>;
  public _clippingContextListForDraw: csmVector<CubismClippingContext>;
  public _clippingMaskBufferSize: number;

  private _tmpMatrix: CubismMatrix44;
  private _tmpMatrixForMask: CubismMatrix44;
  private _tmpMatrixForDraw: CubismMatrix44;
  private _tmpBoundsOnModel: csmRect;

  gl: WebGLRenderingContext;
}


export class CubismRenderTextureResource {
  
  public constructor(frameNo: number, texture: WebGLFramebuffer) {
    this.frameNo = frameNo;
    this.texture = texture;
  }

  public frameNo: number;
  public texture: WebGLFramebuffer;
}


export class CubismClippingContext {
  
  public constructor(
    manager: CubismClippingManager_WebGL,
    clippingDrawableIndices: Int32Array,
    clipCount: number
  ) {
    this._owner = manager;
    this._clippingIdList = clippingDrawableIndices;
    this._clippingIdCount = clipCount;

    this._allClippedDrawRect = new csmRect();
    this._layoutBounds = new csmRect();

    this._clippedDrawableIndexList = [];

    this._matrixForMask = new CubismMatrix44();
    this._matrixForDraw = new CubismMatrix44();
  }

  
  public release(): void {
    if (this._layoutBounds != null) {
      this._layoutBounds = null;
    }

    if (this._allClippedDrawRect != null) {
      this._allClippedDrawRect = null;
    }

    if (this._clippedDrawableIndexList != null) {
      this._clippedDrawableIndexList = null;
    }
  }

  
  public addClippedDrawable(drawableIndex: number) {
    this._clippedDrawableIndexList.push(drawableIndex);
  }

  
  public getClippingManager(): CubismClippingManager_WebGL {
    return this._owner;
  }

  public setGl(gl: WebGLRenderingContext): void {
    this._owner.setGL(gl);
  }

  public _isUsing: boolean;
  public readonly _clippingIdList: Int32Array;
  public _clippingIdCount: number;
  public _layoutChannelNo: number;
  public _layoutBounds: csmRect;
  public _allClippedDrawRect: csmRect;
  public _matrixForMask: CubismMatrix44;
  public _matrixForDraw: CubismMatrix44;
  public _clippedDrawableIndexList: number[];

  private _owner: CubismClippingManager_WebGL;
}


export class CubismShader_WebGL {
  
  public static getInstance(): CubismShader_WebGL {
    if (s_instance == null) {
      s_instance = new CubismShader_WebGL();

      return s_instance;
    }
    return s_instance;
  }

  
  public static deleteInstance(): void {
    if (s_instance) {
      s_instance.release();
      s_instance = null;
    }
  }

  
  private constructor() {
    this._shaderSets = new csmVector<CubismShaderSet>();
  }

  
  public release(): void {
    this.releaseShaderProgram();
  }

  
  public setupShaderProgram(
    renderer: CubismRenderer_WebGL,
    textureId: WebGLTexture,
    vertexCount: number,
    vertexArray: Float32Array,
    indexArray: Uint16Array,
    uvArray: Float32Array,
    bufferData: {
      vertex: WebGLBuffer;
      uv: WebGLBuffer;
      index: WebGLBuffer;
    },
    opacity: number,
    colorBlendMode: CubismBlendMode,
    baseColor: CubismTextureColor,
    isPremultipliedAlpha: boolean,
    matrix4x4: CubismMatrix44,
    invertedMask: boolean
  ): void {
    if (!isPremultipliedAlpha) {
      CubismLogError('NoPremultipliedAlpha is not allowed');
    }

    if (this._shaderSets.getSize() == 0) {
      this.generateShaders();
    }
    let SRC_COLOR: number;
    let DST_COLOR: number;
    let SRC_ALPHA: number;
    let DST_ALPHA: number;

    if (renderer.getClippingContextBufferForMask() != null) {
      const shaderSet: CubismShaderSet = this._shaderSets.at(
        ShaderNames.ShaderNames_SetupMask
      );
      this.gl.useProgram(shaderSet.shaderProgram);
      this.gl.activeTexture(this.gl.TEXTURE0);
      this.gl.bindTexture(this.gl.TEXTURE_2D, textureId);
      this.gl.uniform1i(shaderSet.samplerTexture0Location, 0);
      if (bufferData.vertex == null) {
        bufferData.vertex = this.gl.createBuffer();
      }
      this.gl.bindBuffer(this.gl.ARRAY_BUFFER, bufferData.vertex);
      this.gl.bufferData(
        this.gl.ARRAY_BUFFER,
        vertexArray,
        this.gl.DYNAMIC_DRAW
      );
      this.gl.enableVertexAttribArray(shaderSet.attributePositionLocation);
      this.gl.vertexAttribPointer(
        shaderSet.attributePositionLocation,
        2,
        this.gl.FLOAT,
        false,
        0,
        0
      );
      if (bufferData.uv == null) {
        bufferData.uv = this.gl.createBuffer();
      }
      this.gl.bindBuffer(this.gl.ARRAY_BUFFER, bufferData.uv);
      this.gl.bufferData(this.gl.ARRAY_BUFFER, uvArray, this.gl.DYNAMIC_DRAW);
      this.gl.enableVertexAttribArray(shaderSet.attributeTexCoordLocation);
      this.gl.vertexAttribPointer(
        shaderSet.attributeTexCoordLocation,
        2,
        this.gl.FLOAT,
        false,
        0,
        0
      );
      const channelNo: number = renderer.getClippingContextBufferForMask()
        ._layoutChannelNo;
      const colorChannel: CubismTextureColor = renderer
        .getClippingContextBufferForMask()
        .getClippingManager()
        .getChannelFlagAsColor(channelNo);
      this.gl.uniform4f(
        shaderSet.uniformChannelFlagLocation,
        colorChannel.R,
        colorChannel.G,
        colorChannel.B,
        colorChannel.A
      );

      this.gl.uniformMatrix4fv(
        shaderSet.uniformClipMatrixLocation,
        false,
        renderer.getClippingContextBufferForMask()._matrixForMask.getArray()
      );

      const rect: csmRect = renderer.getClippingContextBufferForMask()
        ._layoutBounds;

      this.gl.uniform4f(
        shaderSet.uniformBaseColorLocation,
        rect.x * 2.0 - 1.0,
        rect.y * 2.0 - 1.0,
        rect.getRight() * 2.0 - 1.0,
        rect.getBottom() * 2.0 - 1.0
      );

      SRC_COLOR = this.gl.ZERO;
      DST_COLOR = this.gl.ONE_MINUS_SRC_COLOR;
      SRC_ALPHA = this.gl.ZERO;
      DST_ALPHA = this.gl.ONE_MINUS_SRC_ALPHA;
    }
    else {
      const masked: boolean =
        renderer.getClippingContextBufferForDraw() != null;
      const offset: number = masked ? (invertedMask ? 2 : 1) : 0;

      let shaderSet: CubismShaderSet = new CubismShaderSet();

      switch (colorBlendMode) {
        case CubismBlendMode.CubismBlendMode_Normal:
        default:
          shaderSet = this._shaderSets.at(
            ShaderNames.ShaderNames_NormalPremultipliedAlpha + offset
          );
          SRC_COLOR = this.gl.ONE;
          DST_COLOR = this.gl.ONE_MINUS_SRC_ALPHA;
          SRC_ALPHA = this.gl.ONE;
          DST_ALPHA = this.gl.ONE_MINUS_SRC_ALPHA;
          break;

        case CubismBlendMode.CubismBlendMode_Additive:
          shaderSet = this._shaderSets.at(
            ShaderNames.ShaderNames_AddPremultipliedAlpha + offset
          );
          SRC_COLOR = this.gl.ONE;
          DST_COLOR = this.gl.ONE;
          SRC_ALPHA = this.gl.ZERO;
          DST_ALPHA = this.gl.ONE;
          break;

        case CubismBlendMode.CubismBlendMode_Multiplicative:
          shaderSet = this._shaderSets.at(
            ShaderNames.ShaderNames_MultPremultipliedAlpha + offset
          );
          SRC_COLOR = this.gl.DST_COLOR;
          DST_COLOR = this.gl.ONE_MINUS_SRC_ALPHA;
          SRC_ALPHA = this.gl.ZERO;
          DST_ALPHA = this.gl.ONE;
          break;
      }

      this.gl.useProgram(shaderSet.shaderProgram);
      if (bufferData.vertex == null) {
        bufferData.vertex = this.gl.createBuffer();
      }
      this.gl.bindBuffer(this.gl.ARRAY_BUFFER, bufferData.vertex);
      this.gl.bufferData(
        this.gl.ARRAY_BUFFER,
        vertexArray,
        this.gl.DYNAMIC_DRAW
      );
      this.gl.enableVertexAttribArray(shaderSet.attributePositionLocation);
      this.gl.vertexAttribPointer(
        shaderSet.attributePositionLocation,
        2,
        this.gl.FLOAT,
        false,
        0,
        0
      );
      if (bufferData.uv == null) {
        bufferData.uv = this.gl.createBuffer();
      }
      this.gl.bindBuffer(this.gl.ARRAY_BUFFER, bufferData.uv);
      this.gl.bufferData(this.gl.ARRAY_BUFFER, uvArray, this.gl.DYNAMIC_DRAW);
      this.gl.enableVertexAttribArray(shaderSet.attributeTexCoordLocation);
      this.gl.vertexAttribPointer(
        shaderSet.attributeTexCoordLocation,
        2,
        this.gl.FLOAT,
        false,
        0,
        0
      );

      if (masked) {
        this.gl.activeTexture(this.gl.TEXTURE1);
        const tex: WebGLTexture = renderer
          .getClippingContextBufferForDraw()
          .getClippingManager()
          .getColorBuffer();
        this.gl.bindTexture(this.gl.TEXTURE_2D, tex);
        this.gl.uniform1i(shaderSet.samplerTexture1Location, 1);
        this.gl.uniformMatrix4fv(
          shaderSet.uniformClipMatrixLocation,
          false,
          renderer.getClippingContextBufferForDraw()._matrixForDraw.getArray()
        );
        const channelNo: number = renderer.getClippingContextBufferForDraw()
          ._layoutChannelNo;
        const colorChannel: CubismTextureColor = renderer
          .getClippingContextBufferForDraw()
          .getClippingManager()
          .getChannelFlagAsColor(channelNo);
        this.gl.uniform4f(
          shaderSet.uniformChannelFlagLocation,
          colorChannel.R,
          colorChannel.G,
          colorChannel.B,
          colorChannel.A
        );
      }
      this.gl.activeTexture(this.gl.TEXTURE0);
      this.gl.bindTexture(this.gl.TEXTURE_2D, textureId);
      this.gl.uniform1i(shaderSet.samplerTexture0Location, 0);
      this.gl.uniformMatrix4fv(
        shaderSet.uniformMatrixLocation,
        false,
        matrix4x4.getArray()
      );

      this.gl.uniform4f(
        shaderSet.uniformBaseColorLocation,
        baseColor.R,
        baseColor.G,
        baseColor.B,
        baseColor.A
      );
    }
    if (bufferData.index == null) {
      bufferData.index = this.gl.createBuffer();
    }
    this.gl.bindBuffer(this.gl.ELEMENT_ARRAY_BUFFER, bufferData.index);
    this.gl.bufferData(
      this.gl.ELEMENT_ARRAY_BUFFER,
      indexArray,
      this.gl.DYNAMIC_DRAW
    );
    this.gl.blendFuncSeparate(SRC_COLOR, DST_COLOR, SRC_ALPHA, DST_ALPHA);
  }

  
  public releaseShaderProgram(): void {
    for (let i = 0; i < this._shaderSets.getSize(); i++) {
      this.gl.deleteProgram(this._shaderSets.at(i).shaderProgram);
      this._shaderSets.at(i).shaderProgram = 0;
      this._shaderSets.set(i, void 0);
      this._shaderSets.set(i, null);
    }
  }

  
  public generateShaders(): void {
    for (let i = 0; i < shaderCount; i++) {
      this._shaderSets.pushBack(new CubismShaderSet());
    }

    this._shaderSets.at(0).shaderProgram = this.loadShaderProgram(
      vertexShaderSrcSetupMask,
      fragmentShaderSrcsetupMask
    );

    this._shaderSets.at(1).shaderProgram = this.loadShaderProgram(
      vertexShaderSrc,
      fragmentShaderSrcPremultipliedAlpha
    );
    this._shaderSets.at(2).shaderProgram = this.loadShaderProgram(
      vertexShaderSrcMasked,
      fragmentShaderSrcMaskPremultipliedAlpha
    );
    this._shaderSets.at(3).shaderProgram = this.loadShaderProgram(
      vertexShaderSrcMasked,
      fragmentShaderSrcMaskInvertedPremultipliedAlpha
    );
    this._shaderSets.at(4).shaderProgram = this._shaderSets.at(1).shaderProgram;
    this._shaderSets.at(5).shaderProgram = this._shaderSets.at(2).shaderProgram;
    this._shaderSets.at(6).shaderProgram = this._shaderSets.at(3).shaderProgram;
    this._shaderSets.at(7).shaderProgram = this._shaderSets.at(1).shaderProgram;
    this._shaderSets.at(8).shaderProgram = this._shaderSets.at(2).shaderProgram;
    this._shaderSets.at(9).shaderProgram = this._shaderSets.at(3).shaderProgram;
    this._shaderSets.at(
      0
    ).attributePositionLocation = this.gl.getAttribLocation(
      this._shaderSets.at(0).shaderProgram,
      'a_position'
    );
    this._shaderSets.at(
      0
    ).attributeTexCoordLocation = this.gl.getAttribLocation(
      this._shaderSets.at(0).shaderProgram,
      'a_texCoord'
    );
    this._shaderSets.at(0).samplerTexture0Location = this.gl.getUniformLocation(
      this._shaderSets.at(0).shaderProgram,
      's_texture0'
    );
    this._shaderSets.at(
      0
    ).uniformClipMatrixLocation = this.gl.getUniformLocation(
      this._shaderSets.at(0).shaderProgram,
      'u_clipMatrix'
    );
    this._shaderSets.at(
      0
    ).uniformChannelFlagLocation = this.gl.getUniformLocation(
      this._shaderSets.at(0).shaderProgram,
      'u_channelFlag'
    );
    this._shaderSets.at(
      0
    ).uniformBaseColorLocation = this.gl.getUniformLocation(
      this._shaderSets.at(0).shaderProgram,
      'u_baseColor'
    );
    this._shaderSets.at(
      1
    ).attributePositionLocation = this.gl.getAttribLocation(
      this._shaderSets.at(1).shaderProgram,
      'a_position'
    );
    this._shaderSets.at(
      1
    ).attributeTexCoordLocation = this.gl.getAttribLocation(
      this._shaderSets.at(1).shaderProgram,
      'a_texCoord'
    );
    this._shaderSets.at(1).samplerTexture0Location = this.gl.getUniformLocation(
      this._shaderSets.at(1).shaderProgram,
      's_texture0'
    );
    this._shaderSets.at(1).uniformMatrixLocation = this.gl.getUniformLocation(
      this._shaderSets.at(1).shaderProgram,
      'u_matrix'
    );
    this._shaderSets.at(
      1
    ).uniformBaseColorLocation = this.gl.getUniformLocation(
      this._shaderSets.at(1).shaderProgram,
      'u_baseColor'
    );
    this._shaderSets.at(
      2
    ).attributePositionLocation = this.gl.getAttribLocation(
      this._shaderSets.at(2).shaderProgram,
      'a_position'
    );
    this._shaderSets.at(
      2
    ).attributeTexCoordLocation = this.gl.getAttribLocation(
      this._shaderSets.at(2).shaderProgram,
      'a_texCoord'
    );
    this._shaderSets.at(2).samplerTexture0Location = this.gl.getUniformLocation(
      this._shaderSets.at(2).shaderProgram,
      's_texture0'
    );
    this._shaderSets.at(2).samplerTexture1Location = this.gl.getUniformLocation(
      this._shaderSets.at(2).shaderProgram,
      's_texture1'
    );
    this._shaderSets.at(2).uniformMatrixLocation = this.gl.getUniformLocation(
      this._shaderSets.at(2).shaderProgram,
      'u_matrix'
    );
    this._shaderSets.at(
      2
    ).uniformClipMatrixLocation = this.gl.getUniformLocation(
      this._shaderSets.at(2).shaderProgram,
      'u_clipMatrix'
    );
    this._shaderSets.at(
      2
    ).uniformChannelFlagLocation = this.gl.getUniformLocation(
      this._shaderSets.at(2).shaderProgram,
      'u_channelFlag'
    );
    this._shaderSets.at(
      2
    ).uniformBaseColorLocation = this.gl.getUniformLocation(
      this._shaderSets.at(2).shaderProgram,
      'u_baseColor'
    );
    this._shaderSets.at(
      3
    ).attributePositionLocation = this.gl.getAttribLocation(
      this._shaderSets.at(3).shaderProgram,
      'a_position'
    );
    this._shaderSets.at(
      3
    ).attributeTexCoordLocation = this.gl.getAttribLocation(
      this._shaderSets.at(3).shaderProgram,
      'a_texCoord'
    );
    this._shaderSets.at(3).samplerTexture0Location = this.gl.getUniformLocation(
      this._shaderSets.at(3).shaderProgram,
      's_texture0'
    );
    this._shaderSets.at(3).samplerTexture1Location = this.gl.getUniformLocation(
      this._shaderSets.at(3).shaderProgram,
      's_texture1'
    );
    this._shaderSets.at(3).uniformMatrixLocation = this.gl.getUniformLocation(
      this._shaderSets.at(3).shaderProgram,
      'u_matrix'
    );
    this._shaderSets.at(
      3
    ).uniformClipMatrixLocation = this.gl.getUniformLocation(
      this._shaderSets.at(3).shaderProgram,
      'u_clipMatrix'
    );
    this._shaderSets.at(
      3
    ).uniformChannelFlagLocation = this.gl.getUniformLocation(
      this._shaderSets.at(3).shaderProgram,
      'u_channelFlag'
    );
    this._shaderSets.at(
      3
    ).uniformBaseColorLocation = this.gl.getUniformLocation(
      this._shaderSets.at(3).shaderProgram,
      'u_baseColor'
    );
    this._shaderSets.at(
      4
    ).attributePositionLocation = this.gl.getAttribLocation(
      this._shaderSets.at(4).shaderProgram,
      'a_position'
    );
    this._shaderSets.at(
      4
    ).attributeTexCoordLocation = this.gl.getAttribLocation(
      this._shaderSets.at(4).shaderProgram,
      'a_texCoord'
    );
    this._shaderSets.at(4).samplerTexture0Location = this.gl.getUniformLocation(
      this._shaderSets.at(4).shaderProgram,
      's_texture0'
    );
    this._shaderSets.at(4).uniformMatrixLocation = this.gl.getUniformLocation(
      this._shaderSets.at(4).shaderProgram,
      'u_matrix'
    );
    this._shaderSets.at(
      4
    ).uniformBaseColorLocation = this.gl.getUniformLocation(
      this._shaderSets.at(4).shaderProgram,
      'u_baseColor'
    );
    this._shaderSets.at(
      5
    ).attributePositionLocation = this.gl.getAttribLocation(
      this._shaderSets.at(5).shaderProgram,
      'a_position'
    );
    this._shaderSets.at(
      5
    ).attributeTexCoordLocation = this.gl.getAttribLocation(
      this._shaderSets.at(5).shaderProgram,
      'a_texCoord'
    );
    this._shaderSets.at(5).samplerTexture0Location = this.gl.getUniformLocation(
      this._shaderSets.at(5).shaderProgram,
      's_texture0'
    );
    this._shaderSets.at(5).samplerTexture1Location = this.gl.getUniformLocation(
      this._shaderSets.at(5).shaderProgram,
      's_texture1'
    );
    this._shaderSets.at(5).uniformMatrixLocation = this.gl.getUniformLocation(
      this._shaderSets.at(5).shaderProgram,
      'u_matrix'
    );
    this._shaderSets.at(
      5
    ).uniformClipMatrixLocation = this.gl.getUniformLocation(
      this._shaderSets.at(5).shaderProgram,
      'u_clipMatrix'
    );
    this._shaderSets.at(
      5
    ).uniformChannelFlagLocation = this.gl.getUniformLocation(
      this._shaderSets.at(5).shaderProgram,
      'u_channelFlag'
    );
    this._shaderSets.at(
      5
    ).uniformBaseColorLocation = this.gl.getUniformLocation(
      this._shaderSets.at(5).shaderProgram,
      'u_baseColor'
    );
    this._shaderSets.at(
      6
    ).attributePositionLocation = this.gl.getAttribLocation(
      this._shaderSets.at(6).shaderProgram,
      'a_position'
    );
    this._shaderSets.at(
      6
    ).attributeTexCoordLocation = this.gl.getAttribLocation(
      this._shaderSets.at(6).shaderProgram,
      'a_texCoord'
    );
    this._shaderSets.at(6).samplerTexture0Location = this.gl.getUniformLocation(
      this._shaderSets.at(6).shaderProgram,
      's_texture0'
    );
    this._shaderSets.at(6).samplerTexture1Location = this.gl.getUniformLocation(
      this._shaderSets.at(6).shaderProgram,
      's_texture1'
    );
    this._shaderSets.at(6).uniformMatrixLocation = this.gl.getUniformLocation(
      this._shaderSets.at(6).shaderProgram,
      'u_matrix'
    );
    this._shaderSets.at(
      6
    ).uniformClipMatrixLocation = this.gl.getUniformLocation(
      this._shaderSets.at(6).shaderProgram,
      'u_clipMatrix'
    );
    this._shaderSets.at(
      6
    ).uniformChannelFlagLocation = this.gl.getUniformLocation(
      this._shaderSets.at(6).shaderProgram,
      'u_channelFlag'
    );
    this._shaderSets.at(
      6
    ).uniformBaseColorLocation = this.gl.getUniformLocation(
      this._shaderSets.at(6).shaderProgram,
      'u_baseColor'
    );
    this._shaderSets.at(
      7
    ).attributePositionLocation = this.gl.getAttribLocation(
      this._shaderSets.at(7).shaderProgram,
      'a_position'
    );
    this._shaderSets.at(
      7
    ).attributeTexCoordLocation = this.gl.getAttribLocation(
      this._shaderSets.at(7).shaderProgram,
      'a_texCoord'
    );
    this._shaderSets.at(7).samplerTexture0Location = this.gl.getUniformLocation(
      this._shaderSets.at(7).shaderProgram,
      's_texture0'
    );
    this._shaderSets.at(7).uniformMatrixLocation = this.gl.getUniformLocation(
      this._shaderSets.at(7).shaderProgram,
      'u_matrix'
    );
    this._shaderSets.at(
      7
    ).uniformBaseColorLocation = this.gl.getUniformLocation(
      this._shaderSets.at(7).shaderProgram,
      'u_baseColor'
    );
    this._shaderSets.at(
      8
    ).attributePositionLocation = this.gl.getAttribLocation(
      this._shaderSets.at(8).shaderProgram,
      'a_position'
    );
    this._shaderSets.at(
      8
    ).attributeTexCoordLocation = this.gl.getAttribLocation(
      this._shaderSets.at(8).shaderProgram,
      'a_texCoord'
    );
    this._shaderSets.at(8).samplerTexture0Location = this.gl.getUniformLocation(
      this._shaderSets.at(8).shaderProgram,
      's_texture0'
    );
    this._shaderSets.at(8).samplerTexture1Location = this.gl.getUniformLocation(
      this._shaderSets.at(8).shaderProgram,
      's_texture1'
    );
    this._shaderSets.at(8).uniformMatrixLocation = this.gl.getUniformLocation(
      this._shaderSets.at(8).shaderProgram,
      'u_matrix'
    );
    this._shaderSets.at(
      8
    ).uniformClipMatrixLocation = this.gl.getUniformLocation(
      this._shaderSets.at(8).shaderProgram,
      'u_clipMatrix'
    );
    this._shaderSets.at(
      8
    ).uniformChannelFlagLocation = this.gl.getUniformLocation(
      this._shaderSets.at(8).shaderProgram,
      'u_channelFlag'
    );
    this._shaderSets.at(
      8
    ).uniformBaseColorLocation = this.gl.getUniformLocation(
      this._shaderSets.at(8).shaderProgram,
      'u_baseColor'
    );
    this._shaderSets.at(
      9
    ).attributePositionLocation = this.gl.getAttribLocation(
      this._shaderSets.at(9).shaderProgram,
      'a_position'
    );
    this._shaderSets.at(
      9
    ).attributeTexCoordLocation = this.gl.getAttribLocation(
      this._shaderSets.at(9).shaderProgram,
      'a_texCoord'
    );
    this._shaderSets.at(9).samplerTexture0Location = this.gl.getUniformLocation(
      this._shaderSets.at(9).shaderProgram,
      's_texture0'
    );
    this._shaderSets.at(9).samplerTexture1Location = this.gl.getUniformLocation(
      this._shaderSets.at(9).shaderProgram,
      's_texture1'
    );
    this._shaderSets.at(9).uniformMatrixLocation = this.gl.getUniformLocation(
      this._shaderSets.at(9).shaderProgram,
      'u_matrix'
    );
    this._shaderSets.at(
      9
    ).uniformClipMatrixLocation = this.gl.getUniformLocation(
      this._shaderSets.at(9).shaderProgram,
      'u_clipMatrix'
    );
    this._shaderSets.at(
      9
    ).uniformChannelFlagLocation = this.gl.getUniformLocation(
      this._shaderSets.at(9).shaderProgram,
      'u_channelFlag'
    );
    this._shaderSets.at(
      9
    ).uniformBaseColorLocation = this.gl.getUniformLocation(
      this._shaderSets.at(9).shaderProgram,
      'u_baseColor'
    );
  }

  
  public loadShaderProgram(
    vertexShaderSource: string,
    fragmentShaderSource: string
  ): WebGLProgram {
    let shaderProgram: WebGLProgram = this.gl.createProgram();

    let vertShader = this.compileShaderSource(
      this.gl.VERTEX_SHADER,
      vertexShaderSource
    );

    if (!vertShader) {
      CubismLogError('Vertex shader compile error!');
      return 0;
    }

    let fragShader = this.compileShaderSource(
      this.gl.FRAGMENT_SHADER,
      fragmentShaderSource
    );
    if (!fragShader) {
      CubismLogError('Vertex shader compile error!');
      return 0;
    }
    this.gl.attachShader(shaderProgram, vertShader);
    this.gl.attachShader(shaderProgram, fragShader);
    this.gl.linkProgram(shaderProgram);
    const linkStatus = this.gl.getProgramParameter(
      shaderProgram,
      this.gl.LINK_STATUS
    );
    if (!linkStatus) {
      CubismLogError('Failed to link program: {0}', shaderProgram);

      this.gl.deleteShader(vertShader);
      vertShader = 0;

      this.gl.deleteShader(fragShader);
      fragShader = 0;

      if (shaderProgram) {
        this.gl.deleteProgram(shaderProgram);
        shaderProgram = 0;
      }

      return 0;
    }
    this.gl.deleteShader(vertShader);
    this.gl.deleteShader(fragShader);

    return shaderProgram;
  }

  
  public compileShaderSource(
    shaderType: GLenum,
    shaderSource: string
  ): WebGLProgram {
    const source: string = shaderSource;

    const shader: WebGLProgram = this.gl.createShader(shaderType);
    this.gl.shaderSource(shader, source);
    this.gl.compileShader(shader);

    if (!shader) {
      const log: string = this.gl.getShaderInfoLog(shader);
      CubismLogError('Shader compile log: {0} ', log);
    }

    const status: any = this.gl.getShaderParameter(
      shader,
      this.gl.COMPILE_STATUS
    );
    if (!status) {
      this.gl.deleteShader(shader);
      return null;
    }

    return shader;
  }

  public setGl(gl: WebGLRenderingContext): void {
    this.gl = gl;
  }

  _shaderSets: csmVector<CubismShaderSet>;
  gl: WebGLRenderingContext;
}


export class CubismShaderSet {
  shaderProgram: WebGLProgram;
  attributePositionLocation: GLuint;
  attributeTexCoordLocation: GLuint;
  uniformMatrixLocation: WebGLUniformLocation;
  uniformClipMatrixLocation: WebGLUniformLocation;
  samplerTexture0Location: WebGLUniformLocation;
  samplerTexture1Location: WebGLUniformLocation;
  uniformBaseColorLocation: WebGLUniformLocation;
  uniformChannelFlagLocation: WebGLUniformLocation;
}

export enum ShaderNames {
  ShaderNames_SetupMask,
  ShaderNames_NormalPremultipliedAlpha,
  ShaderNames_NormalMaskedPremultipliedAlpha,
  ShaderNames_NomralMaskedInvertedPremultipliedAlpha,
  ShaderNames_AddPremultipliedAlpha,
  ShaderNames_AddMaskedPremultipliedAlpha,
  ShaderNames_AddMaskedPremultipliedAlphaInverted,
  ShaderNames_MultPremultipliedAlpha,
  ShaderNames_MultMaskedPremultipliedAlpha,
  ShaderNames_MultMaskedPremultipliedAlphaInverted
}

export const vertexShaderSrcSetupMask =
  'attribute vec4     a_position;' +
  'attribute vec2     a_texCoord;' +
  'varying vec2       v_texCoord;' +
  'varying vec4       v_myPos;' +
  'uniform mat4       u_clipMatrix;' +
  'void main()' +
  '{' +
  '   gl_Position = u_clipMatrix * a_position;' +
  '   v_myPos = u_clipMatrix * a_position;' +
  '   v_texCoord = a_texCoord;' +
  '   v_texCoord.y = 1.0 - v_texCoord.y;' +
  '}';
export const fragmentShaderSrcsetupMask =
  'precision mediump float;' +
  'varying vec2       v_texCoord;' +
  'varying vec4       v_myPos;' +
  'uniform vec4       u_baseColor;' +
  'uniform vec4       u_channelFlag;' +
  'uniform sampler2D  s_texture0;' +
  'void main()' +
  '{' +
  '   float isInside = ' +
  '       step(u_baseColor.x, v_myPos.x/v_myPos.w)' +
  '       * step(u_baseColor.y, v_myPos.y/v_myPos.w)' +
  '       * step(v_myPos.x/v_myPos.w, u_baseColor.z)' +
  '       * step(v_myPos.y/v_myPos.w, u_baseColor.w);' +
  '   gl_FragColor = u_channelFlag * texture2D(s_texture0, v_texCoord).a * isInside;' +
  '}';
export const vertexShaderSrc =
  'attribute vec4     a_position;' +
  'attribute vec2     a_texCoord;' +
  'varying vec2       v_texCoord;' +
  'uniform mat4       u_matrix;' +
  'void main()' +
  '{' +
  '   gl_Position = u_matrix * a_position;' +
  '   v_texCoord = a_texCoord;' +
  '   v_texCoord.y = 1.0 - v_texCoord.y;' +
  '}';
export const vertexShaderSrcMasked =
  'attribute vec4     a_position;' +
  'attribute vec2     a_texCoord;' +
  'varying vec2       v_texCoord;' +
  'varying vec4       v_clipPos;' +
  'uniform mat4       u_matrix;' +
  'uniform mat4       u_clipMatrix;' +
  'void main()' +
  '{' +
  '   gl_Position = u_matrix * a_position;' +
  '   v_clipPos = u_clipMatrix * a_position;' +
  '   v_texCoord = a_texCoord;' +
  '   v_texCoord.y = 1.0 - v_texCoord.y;' +
  '}';
export const fragmentShaderSrcPremultipliedAlpha =
  'precision mediump float;' +
  'varying vec2       v_texCoord;' +
  'uniform vec4       u_baseColor;' +
  'uniform sampler2D  s_texture0;' +
  'void main()' +
  '{' +
  '   gl_FragColor = texture2D(s_texture0 , v_texCoord) * u_baseColor;' +
  '}';
export const fragmentShaderSrcMaskPremultipliedAlpha =
  'precision mediump float;' +
  'varying vec2       v_texCoord;' +
  'varying vec4       v_clipPos;' +
  'uniform vec4       u_baseColor;' +
  'uniform vec4       u_channelFlag;' +
  'uniform sampler2D  s_texture0;' +
  'uniform sampler2D  s_texture1;' +
  'void main()' +
  '{' +
  '   vec4 col_formask = texture2D(s_texture0 , v_texCoord) * u_baseColor;' +
  '   vec4 clipMask = (1.0 - texture2D(s_texture1, v_clipPos.xy / v_clipPos.w)) * u_channelFlag;' +
  '   float maskVal = clipMask.r + clipMask.g + clipMask.b + clipMask.a;' +
  '   col_formask = col_formask * maskVal;' +
  '   gl_FragColor = col_formask;' +
  '}';
export const fragmentShaderSrcMaskInvertedPremultipliedAlpha =
  'precision mediump float;' +
  'varying vec2 v_texCoord;' +
  'varying vec4 v_clipPos;' +
  'uniform sampler2D s_texture0;' +
  'uniform sampler2D s_texture1;' +
  'uniform vec4 u_channelFlag;' +
  'uniform vec4 u_baseColor;' +
  'void main()' +
  '{' +
  'vec4 col_formask = texture2D(s_texture0, v_texCoord) * u_baseColor;' +
  'vec4 clipMask = (1.0 - texture2D(s_texture1, v_clipPos.xy / v_clipPos.w)) * u_channelFlag;' +
  'float maskVal = clipMask.r + clipMask.g + clipMask.b + clipMask.a;' +
  'col_formask = col_formask * (1.0 - maskVal);' +
  'gl_FragColor = col_formask;' +
  '}';


export class CubismRenderer_WebGL extends CubismRenderer {
  
  public initialize(model: CubismModel): void {
    if (model.isUsingMasking()) {
      this._clippingManager = new CubismClippingManager_WebGL();
      this._clippingManager.initialize(
        model,
        model.getDrawableCount(),
        model.getDrawableMasks(),
        model.getDrawableMaskCounts()
      );
    }

    this._sortedDrawableIndexList.resize(model.getDrawableCount(), 0);

    super.initialize(model);
  }

  
  public bindTexture(modelTextureNo: number, glTexture: WebGLTexture): void {
    this._textures.setValue(modelTextureNo, glTexture);
  }

  
  public getBindedTextures(): csmMap<number, WebGLTexture> {
    return this._textures;
  }

  
  public setClippingMaskBufferSize(size: number) {
    this._clippingManager.release();
    this._clippingManager = void 0;
    this._clippingManager = null;

    this._clippingManager = new CubismClippingManager_WebGL();

    this._clippingManager.setClippingMaskBufferSize(size);

    this._clippingManager.initialize(
      this.getModel(),
      this.getModel().getDrawableCount(),
      this.getModel().getDrawableMasks(),
      this.getModel().getDrawableMaskCounts()
    );
  }

  
  public getClippingMaskBufferSize(): number {
    return this._clippingManager.getClippingMaskBufferSize();
  }

  
  public constructor() {
    super();
    this._clippingContextBufferForMask = null;
    this._clippingContextBufferForDraw = null;
    this._clippingManager = new CubismClippingManager_WebGL();
    this.firstDraw = true;
    this._textures = new csmMap<number, number>();
    this._sortedDrawableIndexList = new csmVector<number>();
    this._bufferData = {
      vertex: WebGLBuffer = null,
      uv: WebGLBuffer = null,
      index: WebGLBuffer = null
    };
    this._textures.prepareCapacity(32, true);
  }

  
  public release(): void {
    this._clippingManager.release();
    this._clippingManager = void 0;
    this._clippingManager = null;

    this.gl.deleteBuffer(this._bufferData.vertex);
    this._bufferData.vertex = null;
    this.gl.deleteBuffer(this._bufferData.uv);
    this._bufferData.uv = null;
    this.gl.deleteBuffer(this._bufferData.index);
    this._bufferData.index = null;
    this._bufferData = null;

    this._textures = null;
  }

  
  public doDrawModel(): void {
    if (this._clippingManager != null) {
      this.preDraw();
      this._clippingManager.setupClippingContext(this.getModel(), this);
    }
    this.preDraw();

    const drawableCount: number = this.getModel().getDrawableCount();
    const renderOrder: Int32Array = this.getModel().getDrawableRenderOrders();
    for (let i = 0; i < drawableCount; ++i) {
      const order: number = renderOrder[i];
      this._sortedDrawableIndexList.set(order, i);
    }
    for (let i = 0; i < drawableCount; ++i) {
      const drawableIndex: number = this._sortedDrawableIndexList.at(i);
      if (!this.getModel().getDrawableDynamicFlagIsVisible(drawableIndex)) {
        continue;
      }
      this.setClippingContextBufferForDraw(
        this._clippingManager != null
          ? this._clippingManager
              .getClippingContextListForDraw()
              .at(drawableIndex)
          : null
      );

      this.setIsCulling(this.getModel().getDrawableCulling(drawableIndex));

      this.drawMesh(
        this.getModel().getDrawableTextureIndices(drawableIndex),
        this.getModel().getDrawableVertexIndexCount(drawableIndex),
        this.getModel().getDrawableVertexCount(drawableIndex),
        this.getModel().getDrawableVertexIndices(drawableIndex),
        this.getModel().getDrawableVertices(drawableIndex),
        this.getModel().getDrawableVertexUvs(drawableIndex),
        this.getModel().getDrawableOpacity(drawableIndex),
        this.getModel().getDrawableBlendMode(drawableIndex),
        this.getModel().getDrawableInvertedMaskBit(drawableIndex)
      );
    }
  }

  
  public drawMesh(
    textureNo: number,
    indexCount: number,
    vertexCount: number,
    indexArray: Uint16Array,
    vertexArray: Float32Array,
    uvArray: Float32Array,
    opacity: number,
    colorBlendMode: CubismBlendMode,
    invertedMask: boolean
  ): void {
    if (this.isCulling()) {
      this.gl.enable(this.gl.CULL_FACE);
    } else {
      this.gl.disable(this.gl.CULL_FACE);
    }

    this.gl.frontFace(this.gl.CCW);

    const modelColorRGBA: CubismTextureColor = this.getModelColor();

    if (this.getClippingContextBufferForMask() == null) {
      modelColorRGBA.A *= opacity;
      if (this.isPremultipliedAlpha()) {
        modelColorRGBA.R *= modelColorRGBA.A;
        modelColorRGBA.G *= modelColorRGBA.A;
        modelColorRGBA.B *= modelColorRGBA.A;
      }
    }

    let drawtexture: WebGLTexture;
    if (this._textures.getValue(textureNo) != null) {
      drawtexture = this._textures.getValue(textureNo);
    } else {
      drawtexture = null;
    }

    CubismShader_WebGL.getInstance().setupShaderProgram(
      this,
      drawtexture,
      vertexCount,
      vertexArray,
      indexArray,
      uvArray,
      this._bufferData,
      opacity,
      colorBlendMode,
      modelColorRGBA,
      this.isPremultipliedAlpha(),
      this.getMvpMatrix(),
      invertedMask
    );
    this.gl.drawElements(
      this.gl.TRIANGLES,
      indexCount,
      this.gl.UNSIGNED_SHORT,
      0
    );
    this.gl.useProgram(null);
    this.setClippingContextBufferForDraw(null);
    this.setClippingContextBufferForMask(null);
  }

  
  public static doStaticRelease(): void {
    CubismShader_WebGL.deleteInstance();
  }

  
  public setRenderState(fbo: WebGLFramebuffer, viewport: number[]): void {
    s_fbo = fbo;
    s_viewport = viewport;
  }

  
  public preDraw(): void {
    if (this.firstDraw) {
      this.firstDraw = false;
      this._anisortopy =
        this.gl.getExtension('EXT_texture_filter_anisotropic') ||
        this.gl.getExtension('WEBKIT_EXT_texture_filter_anisotropic') ||
        this.gl.getExtension('MOZ_EXT_texture_filter_anisotropic');
    }

    this.gl.disable(this.gl.SCISSOR_TEST);
    this.gl.disable(this.gl.STENCIL_TEST);
    this.gl.disable(this.gl.DEPTH_TEST);
    this.gl.frontFace(this.gl.CW);

    this.gl.enable(this.gl.BLEND);
    this.gl.colorMask(true, true, true, true);

    this.gl.bindBuffer(this.gl.ARRAY_BUFFER, null);
    this.gl.bindBuffer(this.gl.ELEMENT_ARRAY_BUFFER, null);
  }

  
  public setClippingContextBufferForMask(clip: CubismClippingContext) {
    this._clippingContextBufferForMask = clip;
  }

  
  public getClippingContextBufferForMask(): CubismClippingContext {
    return this._clippingContextBufferForMask;
  }

  
  public setClippingContextBufferForDraw(clip: CubismClippingContext): void {
    this._clippingContextBufferForDraw = clip;
  }

  
  public getClippingContextBufferForDraw(): CubismClippingContext {
    return this._clippingContextBufferForDraw;
  }

  
  public startUp(gl: WebGLRenderingContext): void {
    this.gl = gl;
    this._clippingManager.setGL(gl);
    CubismShader_WebGL.getInstance().setGl(gl);
  }

  _textures: csmMap<number, WebGLTexture>;
  _sortedDrawableIndexList: csmVector<number>;
  _clippingManager: CubismClippingManager_WebGL;
  _clippingContextBufferForMask: CubismClippingContext;
  _clippingContextBufferForDraw: CubismClippingContext;
  firstDraw: boolean;
  _bufferData: {
    vertex: WebGLBuffer;
    uv: WebGLBuffer;
    index: WebGLBuffer;
  };
  gl: WebGLRenderingContext;
}


CubismRenderer.staticRelease = (): void => {
  CubismRenderer_WebGL.doStaticRelease();
};
import * as $ from './cubismrenderer_webgl';
export namespace Live2DCubismFramework {
  export const CubismClippingContext = $.CubismClippingContext;
  export type CubismClippingContext = $.CubismClippingContext;
  export const CubismClippingManager_WebGL = $.CubismClippingManager_WebGL;
  export type CubismClippingManager_WebGL = $.CubismClippingManager_WebGL;
  export const CubismRenderTextureResource = $.CubismRenderTextureResource;
  export type CubismRenderTextureResource = $.CubismRenderTextureResource;
  export const CubismRenderer_WebGL = $.CubismRenderer_WebGL;
  export type CubismRenderer_WebGL = $.CubismRenderer_WebGL;
  export const CubismShaderSet = $.CubismShaderSet;
  export type CubismShaderSet = $.CubismShaderSet;
  export const CubismShader_WebGL = $.CubismShader_WebGL;
  export type CubismShader_WebGL = $.CubismShader_WebGL;
  export const ShaderNames = $.ShaderNames;
  export type ShaderNames = $.ShaderNames;
}

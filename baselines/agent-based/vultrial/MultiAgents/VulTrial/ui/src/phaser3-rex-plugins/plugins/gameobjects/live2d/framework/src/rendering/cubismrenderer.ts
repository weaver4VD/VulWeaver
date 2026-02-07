

import { CubismMatrix44 } from '../math/cubismmatrix44';
import { CubismModel } from '../model/cubismmodel';


export abstract class CubismRenderer {
  
  public static create(): CubismRenderer {
    return null;
  }

  
  public static delete(renderer: CubismRenderer): void {
    renderer = null;
  }

  
  public initialize(model: CubismModel): void {
    this._model = model;
  }

  
  public drawModel(): void {
    if (this.getModel() == null) return;

    this.doDrawModel();
  }

  
  public setMvpMatrix(matrix44: CubismMatrix44): void {
    this._mvpMatrix4x4.setMatrix(matrix44.getArray());
  }

  
  public getMvpMatrix(): CubismMatrix44 {
    return this._mvpMatrix4x4;
  }

  
  public setModelColor(
    red: number,
    green: number,
    blue: number,
    alpha: number
  ): void {
    if (red < 0.0) {
      red = 0.0;
    } else if (red > 1.0) {
      red = 1.0;
    }

    if (green < 0.0) {
      green = 0.0;
    } else if (green > 1.0) {
      green = 1.0;
    }

    if (blue < 0.0) {
      blue = 0.0;
    } else if (blue > 1.0) {
      blue = 1.0;
    }

    if (alpha < 0.0) {
      alpha = 0.0;
    } else if (alpha > 1.0) {
      alpha = 1.0;
    }

    this._modelColor.R = red;
    this._modelColor.G = green;
    this._modelColor.B = blue;
    this._modelColor.A = alpha;
  }

  
  public getModelColor(): CubismTextureColor {
    return JSON.parse(JSON.stringify(this._modelColor));
  }

  
  public setIsPremultipliedAlpha(enable: boolean): void {
    this._isPremultipliedAlpha = enable;
  }

  
  public isPremultipliedAlpha(): boolean {
    return this._isPremultipliedAlpha;
  }

  
  public setIsCulling(culling: boolean): void {
    this._isCulling = culling;
  }

  
  public isCulling(): boolean {
    return this._isCulling;
  }

  
  public setAnisotropy(n: number): void {
    this._anisortopy = n;
  }

  
  public getAnisotropy(): number {
    return this._anisortopy;
  }

  
  public getModel(): CubismModel {
    return this._model;
  }

  
  protected constructor() {
    this._isCulling = false;
    this._isPremultipliedAlpha = false;
    this._anisortopy = 0.0;
    this._model = null;
    this._modelColor = new CubismTextureColor();
    this._mvpMatrix4x4 = new CubismMatrix44();
    this._mvpMatrix4x4.loadIdentity();
  }

  
  public abstract doDrawModel(): void;

  
  public abstract drawMesh(
    textureNo: number,
    indexCount: number,
    vertexCount: number,
    indexArray: Uint16Array,
    vertexArray: Float32Array,
    uvArray: Float32Array,
    opacity: number,
    colorBlendMode: CubismBlendMode,
    invertedMask: boolean
  ): void;

  
  public static staticRelease: Function;

  protected _mvpMatrix4x4: CubismMatrix44;
  protected _modelColor: CubismTextureColor;
  protected _isCulling: boolean;
  protected _isPremultipliedAlpha: boolean;
  protected _anisortopy: any;
  protected _model: CubismModel;
}

export enum CubismBlendMode {
  CubismBlendMode_Normal = 0,
  CubismBlendMode_Additive = 1,
  CubismBlendMode_Multiplicative = 2
}


export class CubismTextureColor {
  
  constructor() {
    this.R = 1.0;
    this.G = 1.0;
    this.B = 1.0;
    this.A = 1.0;
  }

  R: number;
  G: number;
  B: number;
  A: number;
}
import * as $ from './cubismrenderer';
export namespace Live2DCubismFramework {
  export const CubismBlendMode = $.CubismBlendMode;
  export type CubismBlendMode = $.CubismBlendMode;
  export const CubismRenderer = $.CubismRenderer;
  export type CubismRenderer = $.CubismRenderer;
  export const CubismTextureColor = $.CubismTextureColor;
  export type CubismTextureColor = $.CubismTextureColor;
}



import { CubismMatrix44 } from './cubismmatrix44';


export class CubismViewMatrix extends CubismMatrix44 {
  
  public constructor() {
    super();
    this._screenLeft = 0.0;
    this._screenRight = 0.0;
    this._screenTop = 0.0;
    this._screenBottom = 0.0;
    this._maxLeft = 0.0;
    this._maxRight = 0.0;
    this._maxTop = 0.0;
    this._maxBottom = 0.0;
    this._maxScale = 0.0;
    this._minScale = 0.0;
  }

  
  public adjustTranslate(x: number, y: number): void {
    if (this._tr[0] * this._maxLeft + (this._tr[12] + x) > this._screenLeft) {
      x = this._screenLeft - this._tr[0] * this._maxLeft - this._tr[12];
    }

    if (this._tr[0] * this._maxRight + (this._tr[12] + x) < this._screenRight) {
      x = this._screenRight - this._tr[0] * this._maxRight - this._tr[12];
    }

    if (this._tr[5] * this._maxTop + (this._tr[13] + y) < this._screenTop) {
      y = this._screenTop - this._tr[5] * this._maxTop - this._tr[13];
    }

    if (
      this._tr[5] * this._maxBottom + (this._tr[13] + y) >
      this._screenBottom
    ) {
      y = this._screenBottom - this._tr[5] * this._maxBottom - this._tr[13];
    }

    const tr1: Float32Array = new Float32Array([
      1.0,
      0.0,
      0.0,
      0.0,
      0.0,
      1.0,
      0.0,
      0.0,
      0.0,
      0.0,
      1.0,
      0.0,
      x,
      y,
      0.0,
      1.0
    ]);

    CubismMatrix44.multiply(tr1, this._tr, this._tr);
  }

  
  public adjustScale(cx: number, cy: number, scale: number): void {
    const maxScale: number = this.getMaxScale();
    const minScale: number = this.getMinScale();

    const targetScale = scale * this._tr[0];

    if (targetScale < minScale) {
      if (this._tr[0] > 0.0) {
        scale = minScale / this._tr[0];
      }
    } else if (targetScale > maxScale) {
      if (this._tr[0] > 0.0) {
        scale = maxScale / this._tr[0];
      }
    }

    const tr1: Float32Array = new Float32Array([
      1.0,
      0.0,
      0.0,
      0.0,
      0.0,
      1.0,
      0.0,
      0.0,
      0.0,
      0.0,
      1.0,
      0.0,
      cx,
      cy,
      0.0,
      1.0
    ]);

    const tr2: Float32Array = new Float32Array([
      scale,
      0.0,
      0.0,
      0.0,
      0.0,
      scale,
      0.0,
      0.0,
      0.0,
      0.0,
      1.0,
      0.0,
      0.0,
      0.0,
      0.0,
      1.0
    ]);

    const tr3: Float32Array = new Float32Array([
      1.0,
      0.0,
      0.0,
      0.0,
      0.0,
      1.0,
      0.0,
      0.0,
      0.0,
      0.0,
      1.0,
      0.0,
      -cx,
      -cy,
      0.0,
      1.0
    ]);

    CubismMatrix44.multiply(tr3, this._tr, this._tr);
    CubismMatrix44.multiply(tr2, this._tr, this._tr);
    CubismMatrix44.multiply(tr1, this._tr, this._tr);
  }

  
  public setScreenRect(
    left: number,
    right: number,
    bottom: number,
    top: number
  ): void {
    this._screenLeft = left;
    this._screenRight = right;
    this._screenBottom = bottom;
    this._screenTop = top;
  }

  
  public setMaxScreenRect(
    left: number,
    right: number,
    bottom: number,
    top: number
  ): void {
    this._maxLeft = left;
    this._maxRight = right;
    this._maxTop = top;
    this._maxBottom = bottom;
  }

  
  public setMaxScale(maxScale: number): void {
    this._maxScale = maxScale;
  }

  
  public setMinScale(minScale: number): void {
    this._minScale = minScale;
  }

  
  public getMaxScale(): number {
    return this._maxScale;
  }

  
  public getMinScale(): number {
    return this._minScale;
  }

  
  public isMaxScale(): boolean {
    return this.getScaleX() >= this._maxScale;
  }

  
  public isMinScale(): boolean {
    return this.getScaleX() <= this._minScale;
  }

  
  public getScreenLeft(): number {
    return this._screenLeft;
  }

  
  public getScreenRight(): number {
    return this._screenRight;
  }

  
  public getScreenBottom(): number {
    return this._screenBottom;
  }

  
  public getScreenTop(): number {
    return this._screenTop;
  }

  
  public getMaxLeft(): number {
    return this._maxLeft;
  }

  
  public getMaxRight(): number {
    return this._maxRight;
  }

  
  public getMaxBottom(): number {
    return this._maxBottom;
  }

  
  public getMaxTop(): number {
    return this._maxTop;
  }

  private _screenLeft: number;
  private _screenRight: number;
  private _screenTop: number;
  private _screenBottom: number;
  private _maxLeft: number;
  private _maxRight: number;
  private _maxTop: number;
  private _maxBottom: number;
  private _maxScale: number;
  private _minScale: number;
}
import * as $ from './cubismviewmatrix';
export namespace Live2DCubismFramework {
  export const CubismViewMatrix = $.CubismViewMatrix;
  export type CubismViewMatrix = $.CubismViewMatrix;
}

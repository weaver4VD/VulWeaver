

import { csmMap, iterator } from '../type/csmmap';
import { CubismMatrix44 } from './cubismmatrix44';


export class CubismModelMatrix extends CubismMatrix44 {
  
  constructor(w?: number, h?: number) {
    super();

    this._width = w !== undefined ? w : 0.0;
    this._height = h !== undefined ? h : 0.0;

    this.setHeight(2.0);
  }

  
  public setWidth(w: number): void {
    const scaleX: number = w / this._width;
    const scaleY: number = scaleX;
    this.scale(scaleX, scaleY);
  }

  
  public setHeight(h: number): void {
    const scaleX: number = h / this._height;
    const scaleY: number = scaleX;
    this.scale(scaleX, scaleY);
  }

  
  public setPosition(x: number, y: number): void {
    this.translate(x, y);
  }

  
  public setCenterPosition(x: number, y: number) {
    this.centerX(x);
    this.centerY(y);
  }

  
  public top(y: number): void {
    this.setY(y);
  }

  
  public bottom(y: number) {
    const h: number = this._height * this.getScaleY();

    this.translateY(y - h);
  }

  
  public left(x: number): void {
    this.setX(x);
  }

  
  public right(x: number): void {
    const w = this._width * this.getScaleX();

    this.translateX(x - w);
  }

  
  public centerX(x: number): void {
    const w = this._width * this.getScaleX();

    this.translateX(x - w / 2.0);
  }

  
  public setX(x: number): void {
    this.translateX(x);
  }

  
  public centerY(y: number): void {
    const h: number = this._height * this.getScaleY();

    this.translateY(y - h / 2.0);
  }

  
  public setY(y: number): void {
    this.translateY(y);
  }

  
  public setupFromLayout(layout: csmMap<string, number>): void {
    const keyWidth = 'width';
    const keyHeight = 'height';
    const keyX = 'x';
    const keyY = 'y';
    const keyCenterX = 'center_x';
    const keyCenterY = 'center_y';
    const keyTop = 'top';
    const keyBottom = 'bottom';
    const keyLeft = 'left';
    const keyRight = 'right';

    for (
      const ite: iterator<string, number> = layout.begin();
      ite.notEqual(layout.end());
      ite.preIncrement()
    ) {
      const key: string = ite.ptr().first;
      const value: number = ite.ptr().second;

      if (key == keyWidth) {
        this.setWidth(value);
      } else if (key == keyHeight) {
        this.setHeight(value);
      }
    }

    for (
      const ite: iterator<string, number> = layout.begin();
      ite.notEqual(layout.end());
      ite.preIncrement()
    ) {
      const key: string = ite.ptr().first;
      const value: number = ite.ptr().second;

      if (key == keyX) {
        this.setX(value);
      } else if (key == keyY) {
        this.setY(value);
      } else if (key == keyCenterX) {
        this.centerX(value);
      } else if (key == keyCenterY) {
        this.centerY(value);
      } else if (key == keyTop) {
        this.top(value);
      } else if (key == keyBottom) {
        this.bottom(value);
      } else if (key == keyLeft) {
        this.left(value);
      } else if (key == keyRight) {
        this.right(value);
      }
    }
  }

  private _width: number;
  private _height: number;
}
import * as $ from './cubismmodelmatrix';
export namespace Live2DCubismFramework {
  export const CubismModelMatrix = $.CubismModelMatrix;
  export type CubismModelMatrix = $.CubismModelMatrix;
}

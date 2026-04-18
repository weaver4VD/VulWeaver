


export class csmRect {
  
  public constructor(x?: number, y?: number, w?: number, h?: number) {
    this.x = x;
    this.y = y;
    this.width = w;
    this.height = h;
  }

  
  public getCenterX(): number {
    return this.x + 0.5 * this.width;
  }

  
  public getCenterY(): number {
    return this.y + 0.5 * this.height;
  }

  
  public getRight(): number {
    return this.x + this.width;
  }

  
  public getBottom(): number {
    return this.y + this.height;
  }

  
  public setRect(r: csmRect): void {
    this.x = r.x;
    this.y = r.y;
    this.width = r.width;
    this.height = r.height;
  }

  
  public expand(w: number, h: number) {
    this.x -= w;
    this.y -= h;
    this.width += w * 2.0;
    this.height += h * 2.0;
  }

  public x: number;
  public y: number;
  public width: number;
  public height: number;
}
import * as $ from './csmrectf';
export namespace Live2DCubismFramework {
  export const csmRect = $.csmRect;
  export type csmRect = $.csmRect;
}

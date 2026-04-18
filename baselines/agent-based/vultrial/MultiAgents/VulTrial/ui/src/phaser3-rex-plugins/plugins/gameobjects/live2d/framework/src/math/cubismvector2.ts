


export class CubismVector2 {
  
  public constructor(public x?: number, public y?: number) {
    this.x = x == undefined ? 0.0 : x;

    this.y = y == undefined ? 0.0 : y;
  }

  
  public add(vector2: CubismVector2): CubismVector2 {
    const ret: CubismVector2 = new CubismVector2(0.0, 0.0);
    ret.x = this.x + vector2.x;
    ret.y = this.y + vector2.y;
    return ret;
  }

  
  public substract(vector2: CubismVector2): CubismVector2 {
    const ret: CubismVector2 = new CubismVector2(0.0, 0.0);
    ret.x = this.x - vector2.x;
    ret.y = this.y - vector2.y;
    return ret;
  }

  
  public multiply(vector2: CubismVector2): CubismVector2 {
    const ret: CubismVector2 = new CubismVector2(0.0, 0.0);
    ret.x = this.x * vector2.x;
    ret.y = this.y * vector2.y;
    return ret;
  }

  
  public multiplyByScaler(scalar: number): CubismVector2 {
    return this.multiply(new CubismVector2(scalar, scalar));
  }

  
  public division(vector2: CubismVector2): CubismVector2 {
    const ret: CubismVector2 = new CubismVector2(0.0, 0.0);
    ret.x = this.x / vector2.x;
    ret.y = this.y / vector2.y;
    return ret;
  }

  
  public divisionByScalar(scalar: number): CubismVector2 {
    return this.division(new CubismVector2(scalar, scalar));
  }

  
  public getLength(): number {
    return Math.sqrt(this.x * this.x + this.y * this.y);
  }

  
  public getDistanceWith(a: CubismVector2): number {
    return Math.sqrt(
      (this.x - a.x) * (this.x - a.x) + (this.y - a.y) * (this.y - a.y)
    );
  }

  
  public dot(a: CubismVector2): number {
    return this.x * a.x + this.y * a.y;
  }

  
  public normalize(): void {
    const length: number = Math.pow(this.x * this.x + this.y * this.y, 0.5);

    this.x = this.x / length;
    this.y = this.y / length;
  }

  
  public isEqual(rhs: CubismVector2): boolean {
    return this.x == rhs.x && this.y == rhs.y;
  }

  
  public isNotEqual(rhs: CubismVector2): boolean {
    return !this.isEqual(rhs);
  }
}
import * as $ from './cubismvector2';
export namespace Live2DCubismFramework {
  export const CubismVector2 = $.CubismVector2;
  export type CubismVector2 = $.CubismVector2;
}

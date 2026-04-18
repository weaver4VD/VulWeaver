


export class csmString {
  
  public append(c: string, length?: number): csmString {
    this.s += length !== undefined ? c.substr(0, length) : c;

    return this;
  }

  
  public expansion(length: number, v: string): csmString {
    for (let i = 0; i < length; i++) {
      this.append(v);
    }

    return this;
  }

  
  public getBytes(): number {
    return encodeURIComponent(this.s).replace(/%../g, 'x').length;
  }

  
  public getLength(): number {
    return this.s.length;
  }

  
  public isLess(s: csmString): boolean {
    return this.s < s.s;
  }

  
  public isGreat(s: csmString): boolean {
    return this.s > s.s;
  }

  
  public isEqual(s: string): boolean {
    return this.s == s;
  }

  
  public isEmpty(): boolean {
    return this.s.length == 0;
  }

  
  public constructor(s: string) {
    this.s = s;
  }

  s: string;
}
import * as $ from './csmstring';
export namespace Live2DCubismFramework {
  export const csmString = $.csmString;
  export type csmString = $.csmString;
}

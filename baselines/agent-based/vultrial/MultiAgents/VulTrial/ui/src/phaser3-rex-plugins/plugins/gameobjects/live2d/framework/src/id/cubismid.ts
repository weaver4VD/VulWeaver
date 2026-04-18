

import { csmString } from '../type/csmstring';


export class CubismId {
  
  public getString(): csmString {
    return this._id;
  }

  
  public constructor(id: string | csmString) {
    if (typeof id === 'string') {
      this._id = new csmString(id);
      return;
    }

    this._id = id;
  }

  
  public isEqual(c: string | csmString | CubismId): boolean {
    if (typeof c === 'string') {
      return this._id.isEqual(c);
    } else if (c instanceof csmString) {
      return this._id.isEqual(c.s);
    } else if (c instanceof CubismId) {
      return this._id.isEqual(c._id.s);
    }
    return false;
  }

  
  public isNotEqual(c: string | csmString | CubismId): boolean {
    if (typeof c == 'string') {
      return !this._id.isEqual(c);
    } else if (c instanceof csmString) {
      return !this._id.isEqual(c.s);
    } else if (c instanceof CubismId) {
      return !this._id.isEqual(c._id.s);
    }
    return false;
  }

  private _id: csmString;
}

export declare type CubismIdHandle = CubismId;
import * as $ from './cubismid';
export namespace Live2DCubismFramework {
  export const CubismId = $.CubismId;
  export type CubismId = $.CubismId;
  export type CubismIdHandle = $.CubismIdHandle;
}

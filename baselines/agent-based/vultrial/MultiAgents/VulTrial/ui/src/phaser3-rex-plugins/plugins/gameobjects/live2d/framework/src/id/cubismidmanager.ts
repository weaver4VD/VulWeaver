

import { csmString } from '../type/csmstring';
import { csmVector } from '../type/csmvector';
import { CubismId } from './cubismid';


export class CubismIdManager {
  
  public constructor() {
    this._ids = new csmVector<CubismId>();
  }

  
  public release(): void {
    for (let i = 0; i < this._ids.getSize(); ++i) {
      this._ids.set(i, void 0);
    }
    this._ids = null;
  }

  
  public registerIds(ids: string[] | csmString[]): void {
    for (let i = 0; i < ids.length; i++) {
      this.registerId(ids[i]);
    }
  }

  
  public registerId(id: string | csmString): CubismId {
    let result: CubismId = null;

    if ('string' == typeof id) {
      if ((result = this.findId(id)) != null) {
        return result;
      }

      result = new CubismId(id);
      this._ids.pushBack(result);
    } else {
      return this.registerId(id.s);
    }

    return result;
  }

  
  public getId(id: csmString | string): CubismId {
    return this.registerId(id);
  }

  
  public isExist(id: csmString | string): boolean {
    if ('string' == typeof id) {
      return this.findId(id) != null;
    }
    return this.isExist(id.s);
  }

  
  private findId(id: string): CubismId {
    for (let i = 0; i < this._ids.getSize(); ++i) {
      if (
        this._ids
          .at(i)
          .getString()
          .isEqual(id)
      ) {
        return this._ids.at(i);
      }
    }

    return null;
  }

  private _ids: csmVector<CubismId>;
}
import * as $ from './cubismidmanager';
export namespace Live2DCubismFramework {
  export const CubismIdManager = $.CubismIdManager;
  export type CubismIdManager = $.CubismIdManager;
}

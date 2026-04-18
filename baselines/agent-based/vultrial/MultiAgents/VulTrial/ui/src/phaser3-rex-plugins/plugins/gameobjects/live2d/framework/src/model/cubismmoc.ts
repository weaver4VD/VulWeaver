

import { CSM_ASSERT } from '../utils/cubismdebug';
import { CubismModel } from './cubismmodel';


export class CubismMoc {
  
  public static create(mocBytes: ArrayBuffer): CubismMoc {
    let cubismMoc: CubismMoc = null;
    const moc: Live2DCubismCore.Moc = Live2DCubismCore.Moc.fromArrayBuffer(
      mocBytes
    );

    if (moc) {
      cubismMoc = new CubismMoc(moc);
    }

    return cubismMoc;
  }

  
  public static delete(moc: CubismMoc): void {
    moc._moc._release();
    moc._moc = null;
    moc = null;
  }

  
  createModel(): CubismModel {
    let cubismModel: CubismModel = null;

    const model: Live2DCubismCore.Model = Live2DCubismCore.Model.fromMoc(
      this._moc
    );

    if (model) {
      cubismModel = new CubismModel(model);
      cubismModel.initialize();

      ++this._modelCount;
    }

    return cubismModel;
  }

  
  deleteModel(model: CubismModel): void {
    if (model != null) {
      model.release();
      model = null;
      --this._modelCount;
    }
  }

  
  private constructor(moc: Live2DCubismCore.Moc) {
    this._moc = moc;
    this._modelCount = 0;
  }

  
  public release(): void {
    CSM_ASSERT(this._modelCount == 0);

    this._moc._release();
    this._moc = null;
  }

  _moc: Live2DCubismCore.Moc;
  _modelCount: number;
}
import * as $ from './cubismmoc';
export namespace Live2DCubismFramework {
  export const CubismMoc = $.CubismMoc;
  export type CubismMoc = $.CubismMoc;
}

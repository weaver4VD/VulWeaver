

import { CubismIdHandle } from '../id/cubismid';
import { CubismFramework } from '../live2dcubismframework';
import { CubismJson } from '../utils/cubismjson';

const Meta = 'Meta';
const UserDataCount = 'UserDataCount';
const TotalUserDataSize = 'TotalUserDataSize';
const UserData = 'UserData';
const Target = 'Target';
const Id = 'Id';
const Value = 'Value';

export class CubismModelUserDataJson {
  
  public constructor(buffer: ArrayBuffer, size: number) {
    this._json = CubismJson.create(buffer, size);
  }

  
  public release(): void {
    CubismJson.delete(this._json);
  }

  
  public getUserDataCount(): number {
    return this._json
      .getRoot()
      .getValueByString(Meta)
      .getValueByString(UserDataCount)
      .toInt();
  }

  
  public getTotalUserDataSize(): number {
    return this._json
      .getRoot()
      .getValueByString(Meta)
      .getValueByString(TotalUserDataSize)
      .toInt();
  }

  
  public getUserDataTargetType(i: number): string {
    return this._json
      .getRoot()
      .getValueByString(UserData)
      .getValueByIndex(i)
      .getValueByString(Target)
      .getRawString();
  }

  
  public getUserDataId(i: number): CubismIdHandle {
    return CubismFramework.getIdManager().getId(
      this._json
        .getRoot()
        .getValueByString(UserData)
        .getValueByIndex(i)
        .getValueByString(Id)
        .getRawString()
    );
  }

  
  public getUserDataValue(i: number): string {
    return this._json
      .getRoot()
      .getValueByString(UserData)
      .getValueByIndex(i)
      .getValueByString(Value)
      .getRawString();
  }

  private _json: CubismJson;
}
import * as $ from './cubismmodeluserdatajson';
export namespace Live2DCubismFramework {
  export const CubismModelUserDataJson = $.CubismModelUserDataJson;
  export type CubismModelUserDataJson = $.CubismModelUserDataJson;
}

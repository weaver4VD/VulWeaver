

import { CubismIdHandle } from '../id/cubismid';
import { CubismFramework } from '../live2dcubismframework';
import { csmString } from '../type/csmstring';
import { csmVector } from '../type/csmvector';
import { CubismModelUserDataJson } from './cubismmodeluserdatajson';

const ArtMesh = 'ArtMesh';


export class CubismModelUserDataNode {
  targetType: CubismIdHandle;
  targetId: CubismIdHandle;
  value: csmString;
}


export class CubismModelUserData {
  
  public static create(buffer: ArrayBuffer, size: number): CubismModelUserData {
    const ret: CubismModelUserData = new CubismModelUserData();

    ret.parseUserData(buffer, size);

    return ret;
  }

  
  public static delete(modelUserData: CubismModelUserData): void {
    if (modelUserData != null) {
      modelUserData.release();
      modelUserData = null;
    }
  }

  
  public getArtMeshUserDatas(): csmVector<CubismModelUserDataNode> {
    return this._artMeshUserDataNode;
  }

  
  public parseUserData(buffer: ArrayBuffer, size: number): void {
    let json: CubismModelUserDataJson = new CubismModelUserDataJson(
      buffer,
      size
    );

    const typeOfArtMesh = CubismFramework.getIdManager().getId(ArtMesh);
    const nodeCount: number = json.getUserDataCount();

    for (let i = 0; i < nodeCount; i++) {
      const addNode: CubismModelUserDataNode = new CubismModelUserDataNode();

      addNode.targetId = json.getUserDataId(i);
      addNode.targetType = CubismFramework.getIdManager().getId(
        json.getUserDataTargetType(i)
      );
      addNode.value = new csmString(json.getUserDataValue(i));
      this._userDataNodes.pushBack(addNode);

      if (addNode.targetType == typeOfArtMesh) {
        this._artMeshUserDataNode.pushBack(addNode);
      }
    }

    json.release();
    json = void 0;
  }

  
  public constructor() {
    this._userDataNodes = new csmVector<CubismModelUserDataNode>();
    this._artMeshUserDataNode = new csmVector<CubismModelUserDataNode>();
  }

  
  public release(): void {
    for (let i = 0; i < this._userDataNodes.getSize(); ++i) {
      this._userDataNodes.set(i, null);
    }

    this._userDataNodes = null;
  }

  private _userDataNodes: csmVector<CubismModelUserDataNode>;
  private _artMeshUserDataNode: csmVector<CubismModelUserDataNode>;
}
import * as $ from './cubismmodeluserdata';
export namespace Live2DCubismFramework {
  export const CubismModelUserData = $.CubismModelUserData;
  export type CubismModelUserData = $.CubismModelUserData;
  export const CubismModelUserDataNode = $.CubismModelUserDataNode;
  export type CubismModelUserDataNode = $.CubismModelUserDataNode;
}

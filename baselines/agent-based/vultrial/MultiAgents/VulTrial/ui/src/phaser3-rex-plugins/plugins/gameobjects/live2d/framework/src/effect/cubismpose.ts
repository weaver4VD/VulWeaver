

import { CubismIdHandle } from '../id/cubismid';
import { CubismFramework } from '../live2dcubismframework';
import { CubismModel } from '../model/cubismmodel';
import { csmVector, iterator } from '../type/csmvector';
import { CubismJson, Value } from '../utils/cubismjson';

const Epsilon = 0.001;
const DefaultFadeInSeconds = 0.5;
const FadeIn = 'FadeInTime';
const Link = 'Link';
const Groups = 'Groups';
const Id = 'Id';


export class CubismPose {
  
  public static create(pose3json: ArrayBuffer, size: number): CubismPose {
    const ret: CubismPose = new CubismPose();
    const json: CubismJson = CubismJson.create(pose3json, size);
    const root: Value = json.getRoot();
    if (!root.getValueByString(FadeIn).isNull()) {
      ret._fadeTimeSeconds = root
        .getValueByString(FadeIn)
        .toFloat(DefaultFadeInSeconds);

      if (ret._fadeTimeSeconds <= 0.0) {
        ret._fadeTimeSeconds = DefaultFadeInSeconds;
      }
    }
    const poseListInfo: Value = root.getValueByString(Groups);
    const poseCount: number = poseListInfo.getSize();

    for (let poseIndex = 0; poseIndex < poseCount; ++poseIndex) {
      const idListInfo: Value = poseListInfo.getValueByIndex(poseIndex);
      const idCount: number = idListInfo.getSize();
      let groupCount = 0;

      for (let groupIndex = 0; groupIndex < idCount; ++groupIndex) {
        const partInfo: Value = idListInfo.getValueByIndex(groupIndex);
        const partData: PartData = new PartData();
        const parameterId: CubismIdHandle = CubismFramework.getIdManager().getId(
          partInfo.getValueByString(Id).getRawString()
        );

        partData.partId = parameterId;
        if (!partInfo.getValueByString(Link).isNull()) {
          const linkListInfo: Value = partInfo.getValueByString(Link);
          const linkCount: number = linkListInfo.getSize();

          for (let linkIndex = 0; linkIndex < linkCount; ++linkIndex) {
            const linkPart: PartData = new PartData();
            const linkId: CubismIdHandle = CubismFramework.getIdManager().getId(
              linkListInfo.getValueByIndex(linkIndex).getString()
            );

            linkPart.partId = linkId;

            partData.link.pushBack(linkPart);
          }
        }

        ret._partGroups.pushBack(partData.clone());

        ++groupCount;
      }

      ret._partGroupCounts.pushBack(groupCount);
    }

    CubismJson.delete(json);

    return ret;
  }

  
  public static delete(pose: CubismPose): void {
    if (pose != null) {
      pose = null;
    }
  }

  
  public updateParameters(model: CubismModel, deltaTimeSeconds: number): void {
    if (model != this._lastModel) {
      this.reset(model);
    }

    this._lastModel = model;
    if (deltaTimeSeconds < 0.0) {
      deltaTimeSeconds = 0.0;
    }

    let beginIndex = 0;

    for (let i = 0; i < this._partGroupCounts.getSize(); i++) {
      const partGroupCount: number = this._partGroupCounts.at(i);

      this.doFade(model, deltaTimeSeconds, beginIndex, partGroupCount);

      beginIndex += partGroupCount;
    }

    this.copyPartOpacities(model);
  }

  
  public reset(model: CubismModel): void {
    let beginIndex = 0;

    for (let i = 0; i < this._partGroupCounts.getSize(); ++i) {
      const groupCount: number = this._partGroupCounts.at(i);

      for (let j: number = beginIndex; j < beginIndex + groupCount; ++j) {
        this._partGroups.at(j).initialize(model);

        const partsIndex: number = this._partGroups.at(j).partIndex;
        const paramIndex: number = this._partGroups.at(j).parameterIndex;

        if (partsIndex < 0) {
          continue;
        }

        model.setPartOpacityByIndex(partsIndex, j == beginIndex ? 1.0 : 0.0);
        model.setParameterValueByIndex(paramIndex, j == beginIndex ? 1.0 : 0.0);

        for (let k = 0; k < this._partGroups.at(j).link.getSize(); ++k) {
          this._partGroups
            .at(j)
            .link.at(k)
            .initialize(model);
        }
      }

      beginIndex += groupCount;
    }
  }

  
  public copyPartOpacities(model: CubismModel): void {
    for (
      let groupIndex = 0;
      groupIndex < this._partGroups.getSize();
      ++groupIndex
    ) {
      const partData: PartData = this._partGroups.at(groupIndex);

      if (partData.link.getSize() == 0) {
        continue;
      }

      const partIndex: number = this._partGroups.at(groupIndex).partIndex;
      const opacity: number = model.getPartOpacityByIndex(partIndex);

      for (
        let linkIndex = 0;
        linkIndex < partData.link.getSize();
        ++linkIndex
      ) {
        const linkPart: PartData = partData.link.at(linkIndex);
        const linkPartIndex: number = linkPart.partIndex;

        if (linkPartIndex < 0) {
          continue;
        }

        model.setPartOpacityByIndex(linkPartIndex, opacity);
      }
    }
  }

  
  public doFade(
    model: CubismModel,
    deltaTimeSeconds: number,
    beginIndex: number,
    partGroupCount: number
  ): void {
    let visiblePartIndex = -1;
    let newOpacity = 1.0;

    const phi = 0.5;
    const backOpacityThreshold = 0.15;
    for (let i: number = beginIndex; i < beginIndex + partGroupCount; ++i) {
      const partIndex: number = this._partGroups.at(i).partIndex;
      const paramIndex: number = this._partGroups.at(i).parameterIndex;

      if (model.getParameterValueByIndex(paramIndex) > Epsilon) {
        if (visiblePartIndex >= 0) {
          break;
        }

        visiblePartIndex = i;
        newOpacity = model.getPartOpacityByIndex(partIndex);
        newOpacity += deltaTimeSeconds / this._fadeTimeSeconds;

        if (newOpacity > 1.0) {
          newOpacity = 1.0;
        }
      }
    }

    if (visiblePartIndex < 0) {
      visiblePartIndex = 0;
      newOpacity = 1.0;
    }
    for (let i: number = beginIndex; i < beginIndex + partGroupCount; ++i) {
      const partsIndex: number = this._partGroups.at(i).partIndex;
      if (visiblePartIndex == i) {
        model.setPartOpacityByIndex(partsIndex, newOpacity);
      }
      else {
        let opacity: number = model.getPartOpacityByIndex(partsIndex);
        let a1: number;

        if (newOpacity < phi) {
          a1 = (newOpacity * (phi - 1)) / phi + 1.0;
        } else {
          a1 = ((1 - newOpacity) * phi) / (1.0 - phi);
        }
        const backOpacity: number = (1.0 - a1) * (1.0 - newOpacity);

        if (backOpacity > backOpacityThreshold) {
          a1 = 1.0 - backOpacityThreshold / (1.0 - newOpacity);
        }

        if (opacity > a1) {
          opacity = a1;
        }

        model.setPartOpacityByIndex(partsIndex, opacity);
      }
    }
  }

  
  public constructor() {
    this._fadeTimeSeconds = DefaultFadeInSeconds;
    this._lastModel = null;
    this._partGroups = new csmVector<PartData>();
    this._partGroupCounts = new csmVector<number>();
  }

  _partGroups: csmVector<PartData>;
  _partGroupCounts: csmVector<number>;
  _fadeTimeSeconds: number;
  _lastModel: CubismModel;
}


export class PartData {
  
  constructor(v?: PartData) {
    this.parameterIndex = 0;
    this.partIndex = 0;
    this.link = new csmVector<PartData>();

    if (v != undefined) {
      this.partId = v.partId;

      for (
        const ite: iterator<PartData> = v.link.begin();
        ite.notEqual(v.link.end());
        ite.preIncrement()
      ) {
        this.link.pushBack(ite.ptr().clone());
      }
    }
  }

  
  public assignment(v: PartData): PartData {
    this.partId = v.partId;

    for (
      const ite: iterator<PartData> = v.link.begin();
      ite.notEqual(v.link.end());
      ite.preIncrement()
    ) {
      this.link.pushBack(ite.ptr().clone());
    }

    return this;
  }

  
  public initialize(model: CubismModel): void {
    this.parameterIndex = model.getParameterIndex(this.partId);
    this.partIndex = model.getPartIndex(this.partId);

    model.setParameterValueByIndex(this.parameterIndex, 1);
  }

  
  public clone(): PartData {
    const clonePartData: PartData = new PartData();

    clonePartData.partId = this.partId;
    clonePartData.parameterIndex = this.parameterIndex;
    clonePartData.partIndex = this.partIndex;
    clonePartData.link = new csmVector<PartData>();

    for (
      let ite: iterator<PartData> = this.link.begin();
      ite.notEqual(this.link.end());
      ite.increment()
    ) {
      clonePartData.link.pushBack(ite.ptr().clone());
    }

    return clonePartData;
  }

  partId: CubismIdHandle;
  parameterIndex: number;
  partIndex: number;
  link: csmVector<PartData>;
}
import * as $ from './cubismpose';
export namespace Live2DCubismFramework {
  export const CubismPose = $.CubismPose;
  export type CubismPose = $.CubismPose;
  export const PartData = $.PartData;
  export type PartData = $.PartData;
}

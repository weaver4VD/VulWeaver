

import { ICubismModelSetting } from './icubismmodelsetting';
import { CubismIdHandle } from './id/cubismid';
import { CubismFramework } from './live2dcubismframework';
import { csmMap, iterator } from './type/csmmap';
import { csmVector } from './type/csmvector';
import { CubismJson, Value } from './utils/cubismjson';


const Version = 'Version';
const FileReferences = 'FileReferences';
const Groups = 'Groups';
const Layout = 'Layout';
const HitAreas = 'HitAreas';

const Moc = 'Moc';
const Textures = 'Textures';
const Physics = 'Physics';
const Pose = 'Pose';
const Expressions = 'Expressions';
const Motions = 'Motions';

const UserData = 'UserData';
const Name = 'Name';
const FilePath = 'File';
const Id = 'Id';
const Ids = 'Ids';
const Target = 'Target';
const Idle = 'Idle';
const TapBody = 'TapBody';
const PinchIn = 'PinchIn';
const PinchOut = 'PinchOut';
const Shake = 'Shake';
const FlickHead = 'FlickHead';
const Parameter = 'Parameter';

const SoundPath = 'Sound';
const FadeInTime = 'FadeInTime';
const FadeOutTime = 'FadeOutTime';
const CenterX = 'CenterX';
const CenterY = 'CenterY';
const X = 'X';
const Y = 'Y';
const Width = 'Width';
const Height = 'Height';

const LipSync = 'LipSync';
const EyeBlink = 'EyeBlink';

const InitParameter = 'init_param';
const InitPartsVisible = 'init_parts_visible';
const Val = 'val';

enum FrequestNode {
  FrequestNode_Groups,
  FrequestNode_Moc,
  FrequestNode_Motions,
  FrequestNode_Expressions,
  FrequestNode_Textures,
  FrequestNode_Physics,
  FrequestNode_Pose,
  FrequestNode_HitAreas
}


export class CubismModelSettingJson extends ICubismModelSetting {
  
  public constructor(buffer: ArrayBuffer, size: number) {
    super();
    this._json = CubismJson.create(buffer, size);

    if (this._json) {
      this._jsonValue = new csmVector<Value>();
      this._jsonValue.pushBack(this._json.getRoot().getValueByString(Groups));
      this._jsonValue.pushBack(
        this._json
          .getRoot()
          .getValueByString(FileReferences)
          .getValueByString(Moc)
      );
      this._jsonValue.pushBack(
        this._json
          .getRoot()
          .getValueByString(FileReferences)
          .getValueByString(Motions)
      );
      this._jsonValue.pushBack(
        this._json
          .getRoot()
          .getValueByString(FileReferences)
          .getValueByString(Expressions)
      );
      this._jsonValue.pushBack(
        this._json
          .getRoot()
          .getValueByString(FileReferences)
          .getValueByString(Textures)
      );
      this._jsonValue.pushBack(
        this._json
          .getRoot()
          .getValueByString(FileReferences)
          .getValueByString(Physics)
      );
      this._jsonValue.pushBack(
        this._json
          .getRoot()
          .getValueByString(FileReferences)
          .getValueByString(Pose)
      );
      this._jsonValue.pushBack(this._json.getRoot().getValueByString(HitAreas));
    }
  }

  
  public release(): void {
    CubismJson.delete(this._json);

    this._jsonValue = null;
  }

  
  public GetJson(): CubismJson {
    return this._json;
  }

  
  public getModelFileName(): string {
    if (!this.isExistModelFile()) {
      return '';
    }
    return this._jsonValue.at(FrequestNode.FrequestNode_Moc).getRawString();
  }

  
  public getTextureCount(): number {
    if (!this.isExistTextureFiles()) {
      return 0;
    }

    return this._jsonValue.at(FrequestNode.FrequestNode_Textures).getSize();
  }

  
  public getTextureDirectory(): string {
    return this._jsonValue
      .at(FrequestNode.FrequestNode_Textures)
      .getRawString();
  }

  
  public getTextureFileName(index: number): string {
    return this._jsonValue
      .at(FrequestNode.FrequestNode_Textures)
      .getValueByIndex(index)
      .getRawString();
  }

  
  public getHitAreasCount(): number {
    if (!this.isExistHitAreas()) {
      return 0;
    }

    return this._jsonValue.at(FrequestNode.FrequestNode_HitAreas).getSize();
  }

  
  public getHitAreaId(index: number): CubismIdHandle {
    return CubismFramework.getIdManager().getId(
      this._jsonValue
        .at(FrequestNode.FrequestNode_HitAreas)
        .getValueByIndex(index)
        .getValueByString(Id)
        .getRawString()
    );
  }

  
  public getHitAreaName(index: number): string {
    return this._jsonValue
      .at(FrequestNode.FrequestNode_HitAreas)
      .getValueByIndex(index)
      .getValueByString(Name)
      .getRawString();
  }

  
  public getPhysicsFileName(): string {
    if (!this.isExistPhysicsFile()) {
      return '';
    }

    return this._jsonValue.at(FrequestNode.FrequestNode_Physics).getRawString();
  }

  
  public getPoseFileName(): string {
    if (!this.isExistPoseFile()) {
      return '';
    }

    return this._jsonValue.at(FrequestNode.FrequestNode_Pose).getRawString();
  }

  
  public getExpressionCount(): number {
    if (!this.isExistExpressionFile()) {
      return 0;
    }

    return this._jsonValue.at(FrequestNode.FrequestNode_Expressions).getSize();
  }

  
  public getExpressionName(index: number): string {
    return this._jsonValue
      .at(FrequestNode.FrequestNode_Expressions)
      .getValueByIndex(index)
      .getValueByString(Name)
      .getRawString();
  }

  
  public getExpressionFileName(index: number): string {
    return this._jsonValue
      .at(FrequestNode.FrequestNode_Expressions)
      .getValueByIndex(index)
      .getValueByString(FilePath)
      .getRawString();
  }

  
  public getMotionGroupCount(): number {
    if (!this.isExistMotionGroups()) {
      return 0;
    }

    return this._jsonValue
      .at(FrequestNode.FrequestNode_Motions)
      .getKeys()
      .getSize();
  }

  
  public getMotionGroupName(index: number): string {
    if (!this.isExistMotionGroups()) {
      return null;
    }

    return this._jsonValue
      .at(FrequestNode.FrequestNode_Motions)
      .getKeys()
      .at(index);
  }

  
  public getMotionCount(groupName: string): number {
    if (!this.isExistMotionGroupName(groupName)) {
      return 0;
    }

    return this._jsonValue
      .at(FrequestNode.FrequestNode_Motions)
      .getValueByString(groupName)
      .getSize();
  }

  
  public getMotionFileName(groupName: string, index: number): string {
    if (!this.isExistMotionGroupName(groupName)) {
      return '';
    }

    return this._jsonValue
      .at(FrequestNode.FrequestNode_Motions)
      .getValueByString(groupName)
      .getValueByIndex(index)
      .getValueByString(FilePath)
      .getRawString();
  }

  
  public getMotionSoundFileName(groupName: string, index: number): string {
    if (!this.isExistMotionSoundFile(groupName, index)) {
      return '';
    }

    return this._jsonValue
      .at(FrequestNode.FrequestNode_Motions)
      .getValueByString(groupName)
      .getValueByIndex(index)
      .getValueByString(SoundPath)
      .getRawString();
  }

  
  public getMotionFadeInTimeValue(groupName: string, index: number): number {
    if (!this.isExistMotionFadeIn(groupName, index)) {
      return -1.0;
    }

    return this._jsonValue
      .at(FrequestNode.FrequestNode_Motions)
      .getValueByString(groupName)
      .getValueByIndex(index)
      .getValueByString(FadeInTime)
      .toFloat();
  }

  
  public getMotionFadeOutTimeValue(groupName: string, index: number): number {
    if (!this.isExistMotionFadeOut(groupName, index)) {
      return -1.0;
    }

    return this._jsonValue
      .at(FrequestNode.FrequestNode_Motions)
      .getValueByString(groupName)
      .getValueByIndex(index)
      .getValueByString(FadeOutTime)
      .toFloat();
  }

  
  public getUserDataFile(): string {
    if (!this.isExistUserDataFile()) {
      return '';
    }

    return this._json
      .getRoot()
      .getValueByString(FileReferences)
      .getValueByString(UserData)
      .getRawString();
  }

  
  public getLayoutMap(outLayoutMap: csmMap<string, number>): boolean {
    const map: csmMap<string, Value> = this._json
      .getRoot()
      .getValueByString(Layout)
      .getMap();

    if (map == null) {
      return false;
    }

    let ret = false;

    for (
      const ite: iterator<string, Value> = map.begin();
      ite.notEqual(map.end());
      ite.preIncrement()
    ) {
      outLayoutMap.setValue(ite.ptr().first, ite.ptr().second.toFloat());
      ret = true;
    }

    return ret;
  }

  
  public getEyeBlinkParameterCount(): number {
    if (!this.isExistEyeBlinkParameters()) {
      return 0;
    }

    let num = 0;
    for (
      let i = 0;
      i < this._jsonValue.at(FrequestNode.FrequestNode_Groups).getSize();
      i++
    ) {
      const refI: Value = this._jsonValue
        .at(FrequestNode.FrequestNode_Groups)
        .getValueByIndex(i);
      if (refI.isNull() || refI.isError()) {
        continue;
      }

      if (refI.getValueByString(Name).getRawString() == EyeBlink) {
        num = refI
          .getValueByString(Ids)
          .getVector()
          .getSize();
        break;
      }
    }

    return num;
  }

  
  public getEyeBlinkParameterId(index: number): CubismIdHandle {
    if (!this.isExistEyeBlinkParameters()) {
      return null;
    }

    for (
      let i = 0;
      i < this._jsonValue.at(FrequestNode.FrequestNode_Groups).getSize();
      i++
    ) {
      const refI: Value = this._jsonValue
        .at(FrequestNode.FrequestNode_Groups)
        .getValueByIndex(i);
      if (refI.isNull() || refI.isError()) {
        continue;
      }

      if (refI.getValueByString(Name).getRawString() == EyeBlink) {
        return CubismFramework.getIdManager().getId(
          refI
            .getValueByString(Ids)
            .getValueByIndex(index)
            .getRawString()
        );
      }
    }
    return null;
  }

  
  public getLipSyncParameterCount(): number {
    if (!this.isExistLipSyncParameters()) {
      return 0;
    }

    let num = 0;
    for (
      let i = 0;
      i < this._jsonValue.at(FrequestNode.FrequestNode_Groups).getSize();
      i++
    ) {
      const refI: Value = this._jsonValue
        .at(FrequestNode.FrequestNode_Groups)
        .getValueByIndex(i);
      if (refI.isNull() || refI.isError()) {
        continue;
      }

      if (refI.getValueByString(Name).getRawString() == LipSync) {
        num = refI
          .getValueByString(Ids)
          .getVector()
          .getSize();
        break;
      }
    }

    return num;
  }

  
  public getLipSyncParameterId(index: number): CubismIdHandle {
    if (!this.isExistLipSyncParameters()) {
      return null;
    }

    for (
      let i = 0;
      i < this._jsonValue.at(FrequestNode.FrequestNode_Groups).getSize();
      i++
    ) {
      const refI: Value = this._jsonValue
        .at(FrequestNode.FrequestNode_Groups)
        .getValueByIndex(i);
      if (refI.isNull() || refI.isError()) {
        continue;
      }

      if (refI.getValueByString(Name).getRawString() == LipSync) {
        return CubismFramework.getIdManager().getId(
          refI
            .getValueByString(Ids)
            .getValueByIndex(index)
            .getRawString()
        );
      }
    }
    return null;
  }

  
  private isExistModelFile(): boolean {
    const node: Value = this._jsonValue.at(FrequestNode.FrequestNode_Moc);
    return !node.isNull() && !node.isError();
  }

  
  private isExistTextureFiles(): boolean {
    const node: Value = this._jsonValue.at(FrequestNode.FrequestNode_Textures);
    return !node.isNull() && !node.isError();
  }

  
  private isExistHitAreas(): boolean {
    const node: Value = this._jsonValue.at(FrequestNode.FrequestNode_HitAreas);
    return !node.isNull() && !node.isError();
  }

  
  private isExistPhysicsFile(): boolean {
    const node: Value = this._jsonValue.at(FrequestNode.FrequestNode_Physics);
    return !node.isNull() && !node.isError();
  }

  
  private isExistPoseFile(): boolean {
    const node: Value = this._jsonValue.at(FrequestNode.FrequestNode_Pose);
    return !node.isNull() && !node.isError();
  }

  
  private isExistExpressionFile(): boolean {
    const node: Value = this._jsonValue.at(
      FrequestNode.FrequestNode_Expressions
    );
    return !node.isNull() && !node.isError();
  }

  
  private isExistMotionGroups(): boolean {
    const node: Value = this._jsonValue.at(FrequestNode.FrequestNode_Motions);
    return !node.isNull() && !node.isError();
  }

  
  private isExistMotionGroupName(groupName: string): boolean {
    const node: Value = this._jsonValue
      .at(FrequestNode.FrequestNode_Motions)
      .getValueByString(groupName);
    return !node.isNull() && !node.isError();
  }

  
  private isExistMotionSoundFile(groupName: string, index: number): boolean {
    const node: Value = this._jsonValue
      .at(FrequestNode.FrequestNode_Motions)
      .getValueByString(groupName)
      .getValueByIndex(index)
      .getValueByString(SoundPath);
    return !node.isNull() && !node.isError();
  }

  
  private isExistMotionFadeIn(groupName: string, index: number): boolean {
    const node: Value = this._jsonValue
      .at(FrequestNode.FrequestNode_Motions)
      .getValueByString(groupName)
      .getValueByIndex(index)
      .getValueByString(FadeInTime);
    return !node.isNull() && !node.isError();
  }

  
  private isExistMotionFadeOut(groupName: string, index: number): boolean {
    const node: Value = this._jsonValue
      .at(FrequestNode.FrequestNode_Motions)
      .getValueByString(groupName)
      .getValueByIndex(index)
      .getValueByString(FadeOutTime);
    return !node.isNull() && !node.isError();
  }

  
  private isExistUserDataFile(): boolean {
    const node: Value = this._json
      .getRoot()
      .getValueByString(FileReferences)
      .getValueByString(UserData);
    return !node.isNull() && !node.isError();
  }

  
  private isExistEyeBlinkParameters(): boolean {
    if (
      this._jsonValue.at(FrequestNode.FrequestNode_Groups).isNull() ||
      this._jsonValue.at(FrequestNode.FrequestNode_Groups).isError()
    ) {
      return false;
    }

    for (
      let i = 0;
      i < this._jsonValue.at(FrequestNode.FrequestNode_Groups).getSize();
      ++i
    ) {
      if (
        this._jsonValue
          .at(FrequestNode.FrequestNode_Groups)
          .getValueByIndex(i)
          .getValueByString(Name)
          .getRawString() == EyeBlink
      ) {
        return true;
      }
    }

    return false;
  }

  
  private isExistLipSyncParameters(): boolean {
    if (
      this._jsonValue.at(FrequestNode.FrequestNode_Groups).isNull() ||
      this._jsonValue.at(FrequestNode.FrequestNode_Groups).isError()
    ) {
      return false;
    }
    for (
      let i = 0;
      i < this._jsonValue.at(FrequestNode.FrequestNode_Groups).getSize();
      ++i
    ) {
      if (
        this._jsonValue
          .at(FrequestNode.FrequestNode_Groups)
          .getValueByIndex(i)
          .getValueByString(Name)
          .getRawString() == LipSync
      ) {
        return true;
      }
    }
    return false;
  }

  private _json: CubismJson;
  private _jsonValue: csmVector<Value>;
}
import * as $ from './cubismmodelsettingjson';
export namespace Live2DCubismFramework {
  export const CubismModelSettingJson = $.CubismModelSettingJson;
  export type CubismModelSettingJson = $.CubismModelSettingJson;
}



import { CubismIdHandle } from './id/cubismid';
import { csmMap } from './type/csmmap';


export abstract class ICubismModelSetting {
  
  public abstract getModelFileName(): string;

  
  public abstract getTextureCount(): number;

  
  public abstract getTextureDirectory(): string;

  
  public abstract getTextureFileName(index: number): string;

  
  public abstract getHitAreasCount(): number;

  
  public abstract getHitAreaId(index: number): CubismIdHandle;

  
  public abstract getHitAreaName(index: number): string;

  
  public abstract getPhysicsFileName(): string;

  
  public abstract getPoseFileName(): string;

  
  public abstract getExpressionCount(): number;

  
  public abstract getExpressionName(index: number): string;

  
  public abstract getExpressionFileName(index: number): string;

  
  public abstract getMotionGroupCount(): number;

  
  public abstract getMotionGroupName(index: number): string;

  
  public abstract getMotionCount(groupName: string): number;

  
  public abstract getMotionFileName(groupName: string, index: number): string;

  
  public abstract getMotionSoundFileName(
    groupName: string,
    index: number
  ): string;

  
  public abstract getMotionFadeInTimeValue(
    groupName: string,
    index: number
  ): number;

  
  public abstract getMotionFadeOutTimeValue(
    groupName: string,
    index: number
  ): number;

  
  public abstract getUserDataFile(): string;

  
  public abstract getLayoutMap(outLayoutMap: csmMap<string, number>): boolean;

  
  public abstract getEyeBlinkParameterCount(): number;

  
  public abstract getEyeBlinkParameterId(index: number): CubismIdHandle;

  
  public abstract getLipSyncParameterCount(): number;

  
  public abstract getLipSyncParameterId(index: number): CubismIdHandle;
}
import * as $ from './icubismmodelsetting';
export namespace Live2DCubismFramework {
  export const ICubismModelSetting = $.ICubismModelSetting;
  export type ICubismModelSetting = $.ICubismModelSetting;
}

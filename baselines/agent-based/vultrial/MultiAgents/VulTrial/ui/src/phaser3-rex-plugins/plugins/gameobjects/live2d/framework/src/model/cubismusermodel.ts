

import { CubismBreath } from '../effect/cubismbreath';
import { CubismEyeBlink } from '../effect/cubismeyeblink';
import { CubismPose } from '../effect/cubismpose';
import { CubismIdHandle } from '../id/cubismid';
import { Constant } from '../live2dcubismframework';
import { CubismModelMatrix } from '../math/cubismmodelmatrix';
import { CubismTargetPoint } from '../math/cubismtargetpoint';
import { ACubismMotion, FinishedMotionCallback } from '../motion/acubismmotion';
import { CubismExpressionMotion } from '../motion/cubismexpressionmotion';
import { CubismMotion } from '../motion/cubismmotion';
import { CubismMotionManager } from '../motion/cubismmotionmanager';
import { CubismMotionQueueManager } from '../motion/cubismmotionqueuemanager';
import { CubismPhysics } from '../physics/cubismphysics';
import { CubismRenderer_WebGL } from '../rendering/cubismrenderer_webgl';
import { csmString } from '../type/csmstring';
import { CubismLogError, CubismLogInfo } from '../utils/cubismdebug';
import { CubismMoc } from './cubismmoc';
import { CubismModel } from './cubismmodel';
import { CubismModelUserData } from './cubismmodeluserdata';


export class CubismUserModel {
  
  public isInitialized(): boolean {
    return this._initialized;
  }

  
  public setInitialized(v: boolean): void {
    this._initialized = v;
  }

  
  public isUpdating(): boolean {
    return this._updating;
  }

  
  public setUpdating(v: boolean): void {
    this._updating = v;
  }

  
  public setDragging(x: number, y: number): void {
    this._dragManager.set(x, y);
  }

  
  public setAcceleration(x: number, y: number, z: number): void {
    this._accelerationX = x;
    this._accelerationY = y;
    this._accelerationZ = z;
  }

  
  public getModelMatrix(): CubismModelMatrix {
    return this._modelMatrix;
  }

  
  public setOpacity(a: number): void {
    this._opacity = a;
  }

  
  public getOpacity(): number {
    return this._opacity;
  }

  
  public loadModel(buffer: ArrayBuffer) {
    this._moc = CubismMoc.create(buffer);
    this._model = this._moc.createModel();
    this._model.saveParameters();

    if (this._moc == null || this._model == null) {
      CubismLogError('Failed to CreateModel().');
      return;
    }

    this._modelMatrix = new CubismModelMatrix(
      this._model.getCanvasWidth(),
      this._model.getCanvasHeight()
    );
  }

  
  public loadMotion = (
    buffer: ArrayBuffer,
    size: number,
    name: string,
    onFinishedMotionHandler?: FinishedMotionCallback
  ) => CubismMotion.create(buffer, size, onFinishedMotionHandler);

  
  public loadExpression(
    buffer: ArrayBuffer,
    size: number,
    name: string
  ): ACubismMotion {
    return CubismExpressionMotion.create(buffer, size);
  }

  
  public loadPose(buffer: ArrayBuffer, size: number): void {
    this._pose = CubismPose.create(buffer, size);
  }

  
  public loadUserData(buffer: ArrayBuffer, size: number): void {
    this._modelUserData = CubismModelUserData.create(buffer, size);
  }

  
  public loadPhysics(buffer: ArrayBuffer, size: number): void {
    this._physics = CubismPhysics.create(buffer, size);
  }

  
  public isHit(
    drawableId: CubismIdHandle,
    pointX: number,
    pointY: number
  ): boolean {
    const drawIndex: number = this._model.getDrawableIndex(drawableId);

    if (drawIndex < 0) {
      return false;
    }

    const count: number = this._model.getDrawableVertexCount(drawIndex);
    const vertices: Float32Array = this._model.getDrawableVertices(drawIndex);

    let left: number = vertices[0];
    let right: number = vertices[0];
    let top: number = vertices[1];
    let bottom: number = vertices[1];

    for (let j = 1; j < count; ++j) {
      const x = vertices[Constant.vertexOffset + j * Constant.vertexStep];
      const y = vertices[Constant.vertexOffset + j * Constant.vertexStep + 1];

      if (x < left) {
        left = x;
      }

      if (x > right) {
        right = x;
      }

      if (y < top) {
        top = y;
      }

      if (y > bottom) {
        bottom = y;
      }
    }

    const tx: number = this._modelMatrix.invertTransformX(pointX);
    const ty: number = this._modelMatrix.invertTransformY(pointY);

    return left <= tx && tx <= right && top <= ty && ty <= bottom;
  }

  
  public getModel(): CubismModel {
    return this._model;
  }

  
  public getRenderer(): CubismRenderer_WebGL {
    return this._renderer;
  }

  
  public createRenderer(): void {
    if (this._renderer) {
      this.deleteRenderer();
    }

    this._renderer = new CubismRenderer_WebGL();
    this._renderer.initialize(this._model);
  }

  
  public deleteRenderer(): void {
    if (this._renderer != null) {
      this._renderer.release();
      this._renderer = null;
    }
  }

  
  public motionEventFired(eventValue: csmString): void {
    CubismLogInfo('{0}', eventValue.s);
  }

  
  public static cubismDefaultMotionEventCallback(
    caller: CubismMotionQueueManager,
    eventValue: csmString,
    customData: CubismUserModel
  ): void {
    const model: CubismUserModel = customData;

    if (model != null) {
      model.motionEventFired(eventValue);
    }
  }

  
  public constructor() {
    this._moc = null;
    this._model = null;
    this._motionManager = null;
    this._expressionManager = null;
    this._eyeBlink = null;
    this._breath = null;
    this._modelMatrix = null;
    this._pose = null;
    this._dragManager = null;
    this._physics = null;
    this._modelUserData = null;
    this._initialized = false;
    this._updating = false;
    this._opacity = 1.0;
    this._lipsync = true;
    this._lastLipSyncValue = 0.0;
    this._dragX = 0.0;
    this._dragY = 0.0;
    this._accelerationX = 0.0;
    this._accelerationY = 0.0;
    this._accelerationZ = 0.0;
    this._debugMode = false;
    this._renderer = null;
    this._motionManager = new CubismMotionManager();
    this._motionManager.setEventCallback(
      CubismUserModel.cubismDefaultMotionEventCallback,
      this
    );
    this._expressionManager = new CubismMotionManager();
    this._dragManager = new CubismTargetPoint();
  }

  
  public release() {
    if (this._motionManager != null) {
      this._motionManager.release();
      this._motionManager = null;
    }

    if (this._expressionManager != null) {
      this._expressionManager.release();
      this._expressionManager = null;
    }

    if (this._moc != null) {
      this._moc.deleteModel(this._model);
      this._moc.release();
      this._moc = null;
    }

    this._modelMatrix = null;

    CubismPose.delete(this._pose);
    CubismEyeBlink.delete(this._eyeBlink);
    CubismBreath.delete(this._breath);

    this._dragManager = null;

    CubismPhysics.delete(this._physics);
    CubismModelUserData.delete(this._modelUserData);

    this.deleteRenderer();
  }

  protected _moc: CubismMoc;
  protected _model: CubismModel;

  protected _motionManager: CubismMotionManager;
  protected _expressionManager: CubismMotionManager;
  protected _eyeBlink: CubismEyeBlink;
  protected _breath: CubismBreath;
  protected _modelMatrix: CubismModelMatrix;
  protected _pose: CubismPose;
  protected _dragManager: CubismTargetPoint;
  protected _physics: CubismPhysics;
  protected _modelUserData: CubismModelUserData;

  protected _initialized: boolean;
  protected _updating: boolean;
  protected _opacity: number;
  protected _lipsync: boolean;
  protected _lastLipSyncValue: number;
  protected _dragX: number;
  protected _dragY: number;
  protected _accelerationX: number;
  protected _accelerationY: number;
  protected _accelerationZ: number;
  protected _debugMode: boolean;

  private _renderer: CubismRenderer_WebGL;
}
import * as $ from './cubismusermodel';
export namespace Live2DCubismFramework {
  export const CubismUserModel = $.CubismUserModel;
  export type CubismUserModel = $.CubismUserModel;
}

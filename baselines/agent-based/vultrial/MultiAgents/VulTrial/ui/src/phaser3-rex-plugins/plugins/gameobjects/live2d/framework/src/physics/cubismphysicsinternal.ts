

import { CubismIdHandle } from '../id/cubismid';
import { CubismVector2 } from '../math/cubismvector2';
import { csmVector } from '../type/csmvector';


export enum CubismPhysicsTargetType {
  CubismPhysicsTargetType_Parameter
}


export enum CubismPhysicsSource {
  CubismPhysicsSource_X,
  CubismPhysicsSource_Y,
  CubismPhysicsSource_Angle
}


export class PhysicsJsonEffectiveForces {
  constructor() {
    this.gravity = new CubismVector2(0, 0);
    this.wind = new CubismVector2(0, 0);
  }
  gravity: CubismVector2;
  wind: CubismVector2;
}


export class CubismPhysicsParameter {
  id: CubismIdHandle;
  targetType: CubismPhysicsTargetType;
}


export class CubismPhysicsNormalization {
  minimum: number;
  maximum: number;
  defalut: number;
}


export class CubismPhysicsParticle {
  constructor() {
    this.initialPosition = new CubismVector2(0, 0);
    this.position = new CubismVector2(0, 0);
    this.lastPosition = new CubismVector2(0, 0);
    this.lastGravity = new CubismVector2(0, 0);
    this.force = new CubismVector2(0, 0);
    this.velocity = new CubismVector2(0, 0);
  }

  initialPosition: CubismVector2;
  mobility: number;
  delay: number;
  acceleration: number;
  radius: number;
  position: CubismVector2;
  lastPosition: CubismVector2;
  lastGravity: CubismVector2;
  force: CubismVector2;
  velocity: CubismVector2;
}


export class CubismPhysicsSubRig {
  constructor() {
    this.normalizationPosition = new CubismPhysicsNormalization();
    this.normalizationAngle = new CubismPhysicsNormalization();
  }
  inputCount: number;
  outputCount: number;
  particleCount: number;
  baseInputIndex: number;
  baseOutputIndex: number;
  baseParticleIndex: number;
  normalizationPosition: CubismPhysicsNormalization;
  normalizationAngle: CubismPhysicsNormalization;
}


export interface normalizedPhysicsParameterValueGetter {
  (
    targetTranslation: CubismVector2,
    targetAngle: { angle: number },
    value: number,
    parameterMinimunValue: number,
    parameterMaximumValue: number,
    parameterDefaultValue: number,
    normalizationPosition: CubismPhysicsNormalization,
    normalizationAngle: CubismPhysicsNormalization,
    isInverted: boolean,
    weight: number
  ): void;
}


export interface physicsValueGetter {
  (
    translation: CubismVector2,
    particles: CubismPhysicsParticle[],
    particleIndex: number,
    isInverted: boolean,
    parentGravity: CubismVector2
  ): number;
}


export interface physicsScaleGetter {
  (translationScale: CubismVector2, angleScale: number): number;
}


export class CubismPhysicsInput {
  constructor() {
    this.source = new CubismPhysicsParameter();
  }
  source: CubismPhysicsParameter;
  sourceParameterIndex: number;
  weight: number;
  type: number;
  reflect: boolean;
  getNormalizedParameterValue: normalizedPhysicsParameterValueGetter;
}


export class CubismPhysicsOutput {
  constructor() {
    this.destination = new CubismPhysicsParameter();
    this.translationScale = new CubismVector2(0, 0);
  }

  destination: CubismPhysicsParameter;
  destinationParameterIndex: number;
  vertexIndex: number;
  translationScale: CubismVector2;
  angleScale: number;
  weight: number;
  type: CubismPhysicsSource;
  reflect: boolean;
  valueBelowMinimum: number;
  valueExceededMaximum: number;
  getValue: physicsValueGetter;
  getScale: physicsScaleGetter;
}


export class CubismPhysicsRig {
  constructor() {
    this.settings = new csmVector<CubismPhysicsSubRig>();
    this.inputs = new csmVector<CubismPhysicsInput>();
    this.outputs = new csmVector<CubismPhysicsOutput>();
    this.particles = new csmVector<CubismPhysicsParticle>();
    this.gravity = new CubismVector2(0, 0);
    this.wind = new CubismVector2(0, 0);
  }

  subRigCount: number;
  settings: csmVector<CubismPhysicsSubRig>;
  inputs: csmVector<CubismPhysicsInput>;
  outputs: csmVector<CubismPhysicsOutput>;
  particles: csmVector<CubismPhysicsParticle>;
  gravity: CubismVector2;
  wind: CubismVector2;
}
import * as $ from './cubismphysicsinternal';
export namespace Live2DCubismFramework {
  export const CubismPhysicsInput = $.CubismPhysicsInput;
  export type CubismPhysicsInput = $.CubismPhysicsInput;
  export const CubismPhysicsNormalization = $.CubismPhysicsNormalization;
  export type CubismPhysicsNormalization = $.CubismPhysicsNormalization;
  export const CubismPhysicsOutput = $.CubismPhysicsOutput;
  export type CubismPhysicsOutput = $.CubismPhysicsOutput;
  export const CubismPhysicsParameter = $.CubismPhysicsParameter;
  export type CubismPhysicsParameter = $.CubismPhysicsParameter;
  export const CubismPhysicsParticle = $.CubismPhysicsParticle;
  export type CubismPhysicsParticle = $.CubismPhysicsParticle;
  export const CubismPhysicsRig = $.CubismPhysicsRig;
  export type CubismPhysicsRig = $.CubismPhysicsRig;
  export const CubismPhysicsSource = $.CubismPhysicsSource;
  export type CubismPhysicsSource = $.CubismPhysicsSource;
  export const CubismPhysicsSubRig = $.CubismPhysicsSubRig;
  export type CubismPhysicsSubRig = $.CubismPhysicsSubRig;
  export const CubismPhysicsTargetType = $.CubismPhysicsTargetType;
  export type CubismPhysicsTargetType = $.CubismPhysicsTargetType;
  export const PhysicsJsonEffectiveForces = $.PhysicsJsonEffectiveForces;
  export type PhysicsJsonEffectiveForces = $.PhysicsJsonEffectiveForces;
  export type normalizedPhysicsParameterValueGetter = $.normalizedPhysicsParameterValueGetter;
  export type physicsScaleGetter = $.physicsScaleGetter;
  export type physicsValueGetter = $.physicsValueGetter;
}

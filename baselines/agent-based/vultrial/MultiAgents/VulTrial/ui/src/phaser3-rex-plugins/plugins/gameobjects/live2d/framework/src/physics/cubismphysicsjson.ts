

import { CubismIdHandle } from '../id/cubismid';
import { CubismFramework } from '../live2dcubismframework';
import { CubismVector2 } from '../math/cubismvector2';
import { CubismJson } from '../utils/cubismjson';
const Position = 'Position';
const X = 'X';
const Y = 'Y';
const Angle = 'Angle';
const Type = 'Type';
const Id = 'Id';
const Meta = 'Meta';
const EffectiveForces = 'EffectiveForces';
const TotalInputCount = 'TotalInputCount';
const TotalOutputCount = 'TotalOutputCount';
const PhysicsSettingCount = 'PhysicsSettingCount';
const Gravity = 'Gravity';
const Wind = 'Wind';
const VertexCount = 'VertexCount';
const PhysicsSettings = 'PhysicsSettings';
const Normalization = 'Normalization';
const Minimum = 'Minimum';
const Maximum = 'Maximum';
const Default = 'Default';
const Reflect = 'Reflect';
const Weight = 'Weight';
const Input = 'Input';
const Source = 'Source';
const Output = 'Output';
const Scale = 'Scale';
const VertexIndex = 'VertexIndex';
const Destination = 'Destination';
const Vertices = 'Vertices';
const Mobility = 'Mobility';
const Delay = 'Delay';
const Radius = 'Radius';
const Acceleration = 'Acceleration';


export class CubismPhysicsJson {
  
  public constructor(buffer: ArrayBuffer, size: number) {
    this._json = CubismJson.create(buffer, size);
  }

  
  public release(): void {
    CubismJson.delete(this._json);
  }

  
  public getGravity(): CubismVector2 {
    const ret: CubismVector2 = new CubismVector2(0, 0);
    ret.x = this._json
      .getRoot()
      .getValueByString(Meta)
      .getValueByString(EffectiveForces)
      .getValueByString(Gravity)
      .getValueByString(X)
      .toFloat();
    ret.y = this._json
      .getRoot()
      .getValueByString(Meta)
      .getValueByString(EffectiveForces)
      .getValueByString(Gravity)
      .getValueByString(Y)
      .toFloat();
    return ret;
  }

  
  public getWind(): CubismVector2 {
    const ret: CubismVector2 = new CubismVector2(0, 0);
    ret.x = this._json
      .getRoot()
      .getValueByString(Meta)
      .getValueByString(EffectiveForces)
      .getValueByString(Wind)
      .getValueByString(X)
      .toFloat();
    ret.y = this._json
      .getRoot()
      .getValueByString(Meta)
      .getValueByString(EffectiveForces)
      .getValueByString(Wind)
      .getValueByString(Y)
      .toFloat();
    return ret;
  }

  
  public getSubRigCount(): number {
    return this._json
      .getRoot()
      .getValueByString(Meta)
      .getValueByString(PhysicsSettingCount)
      .toInt();
  }

  
  public getTotalInputCount(): number {
    return this._json
      .getRoot()
      .getValueByString(Meta)
      .getValueByString(TotalInputCount)
      .toInt();
  }

  
  public getTotalOutputCount(): number {
    return this._json
      .getRoot()
      .getValueByString(Meta)
      .getValueByString(TotalOutputCount)
      .toInt();
  }

  
  public getVertexCount(): number {
    return this._json
      .getRoot()
      .getValueByString(Meta)
      .getValueByString(VertexCount)
      .toInt();
  }

  
  public getNormalizationPositionMinimumValue(
    physicsSettingIndex: number
  ): number {
    return this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Normalization)
      .getValueByString(Position)
      .getValueByString(Minimum)
      .toFloat();
  }

  
  public getNormalizationPositionMaximumValue(
    physicsSettingIndex: number
  ): number {
    return this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Normalization)
      .getValueByString(Position)
      .getValueByString(Maximum)
      .toFloat();
  }

  
  public getNormalizationPositionDefaultValue(
    physicsSettingIndex: number
  ): number {
    return this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Normalization)
      .getValueByString(Position)
      .getValueByString(Default)
      .toFloat();
  }

  
  public getNormalizationAngleMinimumValue(
    physicsSettingIndex: number
  ): number {
    return this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Normalization)
      .getValueByString(Angle)
      .getValueByString(Minimum)
      .toFloat();
  }

  
  public getNormalizationAngleMaximumValue(
    physicsSettingIndex: number
  ): number {
    return this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Normalization)
      .getValueByString(Angle)
      .getValueByString(Maximum)
      .toFloat();
  }

  
  public getNormalizationAngleDefaultValue(
    physicsSettingIndex: number
  ): number {
    return this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Normalization)
      .getValueByString(Angle)
      .getValueByString(Default)
      .toFloat();
  }

  
  public getInputCount(physicsSettingIndex: number): number {
    return this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Input)
      .getVector()
      .getSize();
  }

  
  public getInputWeight(
    physicsSettingIndex: number,
    inputIndex: number
  ): number {
    return this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Input)
      .getValueByIndex(inputIndex)
      .getValueByString(Weight)
      .toFloat();
  }

  
  public getInputReflect(
    physicsSettingIndex: number,
    inputIndex: number
  ): boolean {
    return this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Input)
      .getValueByIndex(inputIndex)
      .getValueByString(Reflect)
      .toBoolean();
  }

  
  public getInputType(physicsSettingIndex: number, inputIndex: number): string {
    return this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Input)
      .getValueByIndex(inputIndex)
      .getValueByString(Type)
      .getRawString();
  }

  
  public getInputSourceId(
    physicsSettingIndex: number,
    inputIndex: number
  ): CubismIdHandle {
    return CubismFramework.getIdManager().getId(
      this._json
        .getRoot()
        .getValueByString(PhysicsSettings)
        .getValueByIndex(physicsSettingIndex)
        .getValueByString(Input)
        .getValueByIndex(inputIndex)
        .getValueByString(Source)
        .getValueByString(Id)
        .getRawString()
    );
  }

  
  public getOutputCount(physicsSettingIndex: number): number {
    return this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Output)
      .getVector()
      .getSize();
  }

  
  public getOutputVertexIndex(
    physicsSettingIndex: number,
    outputIndex: number
  ): number {
    return this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Output)
      .getValueByIndex(outputIndex)
      .getValueByString(VertexIndex)
      .toInt();
  }

  
  public getOutputAngleScale(
    physicsSettingIndex: number,
    outputIndex: number
  ): number {
    return this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Output)
      .getValueByIndex(outputIndex)
      .getValueByString(Scale)
      .toFloat();
  }

  
  public getOutputWeight(
    physicsSettingIndex: number,
    outputIndex: number
  ): number {
    return this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Output)
      .getValueByIndex(outputIndex)
      .getValueByString(Weight)
      .toFloat();
  }

  
  public getOutputDestinationId(
    physicsSettingIndex: number,
    outputIndex: number
  ): CubismIdHandle {
    return CubismFramework.getIdManager().getId(
      this._json
        .getRoot()
        .getValueByString(PhysicsSettings)
        .getValueByIndex(physicsSettingIndex)
        .getValueByString(Output)
        .getValueByIndex(outputIndex)
        .getValueByString(Destination)
        .getValueByString(Id)
        .getRawString()
    );
  }

  
  public getOutputType(
    physicsSettingIndex: number,
    outputIndex: number
  ): string {
    return this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Output)
      .getValueByIndex(outputIndex)
      .getValueByString(Type)
      .getRawString();
  }

  
  public getOutputReflect(
    physicsSettingIndex: number,
    outputIndex: number
  ): boolean {
    return this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Output)
      .getValueByIndex(outputIndex)
      .getValueByString(Reflect)
      .toBoolean();
  }

  
  public getParticleCount(physicsSettingIndex: number): number {
    return this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Vertices)
      .getVector()
      .getSize();
  }

  
  public getParticleMobility(
    physicsSettingIndex: number,
    vertexIndex: number
  ): number {
    return this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Vertices)
      .getValueByIndex(vertexIndex)
      .getValueByString(Mobility)
      .toFloat();
  }

  
  public getParticleDelay(
    physicsSettingIndex: number,
    vertexIndex: number
  ): number {
    return this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Vertices)
      .getValueByIndex(vertexIndex)
      .getValueByString(Delay)
      .toFloat();
  }

  
  public getParticleAcceleration(
    physicsSettingIndex: number,
    vertexIndex: number
  ): number {
    return this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Vertices)
      .getValueByIndex(vertexIndex)
      .getValueByString(Acceleration)
      .toFloat();
  }

  
  public getParticleRadius(
    physicsSettingIndex: number,
    vertexIndex: number
  ): number {
    return this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Vertices)
      .getValueByIndex(vertexIndex)
      .getValueByString(Radius)
      .toFloat();
  }

  
  public getParticlePosition(
    physicsSettingIndex: number,
    vertexIndex: number
  ): CubismVector2 {
    const ret: CubismVector2 = new CubismVector2(0, 0);
    ret.x = this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Vertices)
      .getValueByIndex(vertexIndex)
      .getValueByString(Position)
      .getValueByString(X)
      .toFloat();
    ret.y = this._json
      .getRoot()
      .getValueByString(PhysicsSettings)
      .getValueByIndex(physicsSettingIndex)
      .getValueByString(Vertices)
      .getValueByIndex(vertexIndex)
      .getValueByString(Position)
      .getValueByString(Y)
      .toFloat();
    return ret;
  }

  _json: CubismJson;
}
import * as $ from './cubismphysicsjson';
export namespace Live2DCubismFramework {
  export const CubismPhysicsJson = $.CubismPhysicsJson;
  export type CubismPhysicsJson = $.CubismPhysicsJson;
}

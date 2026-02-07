import { ACubismMotion } from '../../../framework/src/motion/acubismmotion';
import { CubismEyeBlink } from '../../../framework/src/effect/cubismeyeblink';
import { BreathParameterData, CubismBreath } from '../../../framework/src/effect/cubismbreath';
import { csmVector } from '../../../framework/src/type/csmvector';
import { csmMap } from '../../../framework/src/type/csmmap';

var Setup = function (data) {
    var setting = data.setting;
    this._modelSetting = setting;
    var arrayBuffer = data.model;
    this.loadModel(arrayBuffer, arrayBuffer.byteLength);
    this.createRenderer();
    this.getRenderer().startUp(this._globalData.gl);
    var expressions = data.expressions;
    for (var expressionName in expressions) {
        var arrayBuffer = expressions[expressionName];
        var motion = this.loadExpression(arrayBuffer, arrayBuffer.byteLength, expressionName);

        if (this._expressions.getValue(expressionName) != null) {
            ACubismMotion.delete(this._expressions.getValue(expressionName));
            this._expressions.setValue(expressionName, null);
        }

        this._expressions.setValue(expressionName, motion);
    }
    var arrayBuffer = data.physics;
    if (arrayBuffer) {
        this.loadPhysics(arrayBuffer, arrayBuffer.byteLength);
    }
    var arrayBuffer = data.pose;
    if (arrayBuffer) {
        this.loadPose(arrayBuffer, arrayBuffer.byteLength);
    }
    if (setting.getEyeBlinkParameterCount() > 0) {
        this._eyeBlink = CubismEyeBlink.create(setting);
    }
    this._breath = CubismBreath.create();

    this.registerParameter('angleX');
    this.registerParameter('angleY');
    this.registerParameter('angleZ');
    this.registerParameter('bodyAngleX');
    this.registerParameter('breath');

    var breathParameters = new csmVector();
    breathParameters.pushBack(
        new BreathParameterData(this._idParamAngleX, 0.0, 15.0, 6.5345, 0.5)
    );
    breathParameters.pushBack(
        new BreathParameterData(this._idParamAngleY, 0.0, 8.0, 3.5345, 0.5)
    );
    breathParameters.pushBack(
        new BreathParameterData(this._idParamAngleZ, 0.0, 10.0, 5.5345, 0.5)
    );
    breathParameters.pushBack(
        new BreathParameterData(this._idParamBodyAngleX, 0.0, 4.0, 15.5345, 0.5)
    );
    breathParameters.pushBack(
        new BreathParameterData(this._idParamBreath, 0.5, 0.5, 3.2345, 1)
    );

    this._breath.setParameters(breathParameters);
    var arrayBuffer = data.userData;
    if (arrayBuffer) {
        this.loadUserData(arrayBuffer, arrayBuffer.byteLength);
    }
    var eyeBlinkIdCount = setting.getEyeBlinkParameterCount();
    for (var i = 0; i < eyeBlinkIdCount; i++) {
        this._eyeBlinkIds.pushBack(setting.getEyeBlinkParameterId(i));
    }
    var lipSyncIdCount = setting.getLipSyncParameterCount();
    for (let i = 0; i < lipSyncIdCount; i++) {
        this._lipSyncIds.pushBack(setting.getLipSyncParameterId(i));
    }
    this._model.saveParameters();
    var motionGroups = data.motions;
    for (var groupName in motionGroups) {
        var motionGroup = motionGroups[groupName];
        for (var i in motionGroup) {
            var arrayBuffer = motionGroup[i];
            var motionName = `${groupName}_${i}`;
            var motion = this.loadMotion(arrayBuffer, arrayBuffer.byteLength, motionName);

            i = parseInt(i);
            var fadeTime = setting.getMotionFadeInTimeValue(groupName, i);
            if (fadeTime >= 0.0) {
                motion.setFadeInTime(fadeTime);
            }

            var fadeTime = setting.getMotionFadeOutTimeValue(groupName, i);
            if (fadeTime >= 0.0) {
                motion.setFadeOutTime(fadeTime);
            }

            motion.setEffectIds(this._eyeBlinkIds, this._lipSyncIds);

            if (this._motions.getValue(motionName) != null) {
                ACubismMotion.delete(this._motions.getValue(motionName));
            }

            this._motions.setValue(motionName, motion);
        }

    }
    var textures = data.textures;
    for (var i in textures) {
        this.getRenderer().bindTexture(parseInt(i), textures[i]);
    }
    this._motionManager.stopAllMotions();
    var canvasinfo = this._model._model.canvasinfo;
    this._pixelWidth = canvasinfo.CanvasWidth;
    this._pixelHeight = canvasinfo.CanvasHeight;
    this._pixelsPerUnit = canvasinfo.PixelsPerUnit;
    var layout = new csmMap();
    setting.getLayoutMap(layout);
    this._modelMatrix.setupFromLayout(layout);
    var count = this._modelSetting.getHitAreasCount();
    for (var i = 0; i < count; i++) {
        var hitAreaName = this._modelSetting.getHitAreaName(i);
        this._hitTestResult[hitAreaName] = false;
    }

    return this;
}

export default Setup;
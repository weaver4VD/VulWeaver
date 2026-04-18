import RGBToHSV from '../utils/RGBToHSV.js';
import HSVToRGB from '../utils/HSVToRGB.js';
import IsEdge from '../utils/IsEdge.js';

const frag = `\
#ifdef GL_FRAGMENT_PRECISION_HIGH
#define highmedp highp
#else
#define highmedp mediump
#endif
precision highmedp float;
uniform sampler2D uMainSampler; 
varying vec2 outTexCoord;
uniform vec2 texSize;
uniform float edgeThreshold;
uniform float hStep;
uniform float sStep;
uniform float vStep;
uniform vec3 edgeColor;
`
+ RGBToHSV + IsEdge + HSVToRGB +
`
void main() {
  vec4 front = texture2D(uMainSampler, outTexCoord);  
  vec3 colorLevel;
  if ((hStep > 0.0) || (sStep > 0.0) || (vStep > 0.0)) {
    vec3 colorHsv = RGBToHSV(front.rgb);  
    if (hStep > 0.0) {
      colorHsv.x = min(floor((colorHsv.x / hStep) + 0.5) * hStep, 360.0);
    }
    if (sStep > 0.0) {
      colorHsv.y = min(floor((colorHsv.y / sStep) + 0.5) * sStep, 1.0);
    }
    if (vStep > 0.0) {
      colorHsv.z = min(floor((colorHsv.z / vStep) + 0.5) * vStep, 1.0);
    }
    colorLevel = HSVToRGB(colorHsv.x, colorHsv.y, colorHsv.z);
  } else {
    colorLevel = front.rgb;
  }

  vec3 outColor = (IsEdge(outTexCoord, texSize, edgeThreshold))? edgeColor : colorLevel;
  gl_FragColor = vec4(outColor, front.a);
}
`;

export default frag;
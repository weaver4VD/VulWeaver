
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
uniform vec2 center;
uniform float waveRadius;
uniform float waveHalfWidth;
uniform float powBaseScale;
uniform float powExponent;

void main (void) {
  if (waveHalfWidth > 0.0) {
    vec2 tc = outTexCoord * texSize;
    tc -= center;

    float diff = length(tc) - waveRadius;
    if ((diff <= waveHalfWidth) && (diff >= -waveHalfWidth)) {
      diff /= max(texSize.x, texSize.y);
      float powDiff = 1.0 - pow(abs(diff*powBaseScale), powExponent);
      tc += texSize * diff * powDiff;
    }

    tc += center;
    gl_FragColor = texture2D(uMainSampler, tc / texSize);
  } else {
    gl_FragColor = texture2D(uMainSampler, outTexCoord);
  }
}
`;

export default frag;
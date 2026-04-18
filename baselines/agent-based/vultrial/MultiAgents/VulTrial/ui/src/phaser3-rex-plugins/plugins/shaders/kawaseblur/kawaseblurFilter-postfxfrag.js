const frag = `\
#ifdef GL_FRAGMENT_PRECISION_HIGH
#define highmedp highp
#else
#define highmedp mediump
#endif
precision highmedp float;
uniform sampler2D uMainSampler; 
varying vec2 outTexCoord;
uniform vec2 uOffset;

void main (void) {
  vec4 color = vec4(0.0);
  color += texture2D(uMainSampler, vec2(outTexCoord.x - uOffset.x, outTexCoord.y + uOffset.y));
  color += texture2D(uMainSampler, vec2(outTexCoord.x + uOffset.x, outTexCoord.y + uOffset.y));
  color += texture2D(uMainSampler, vec2(outTexCoord.x + uOffset.x, outTexCoord.y - uOffset.y));
  color += texture2D(uMainSampler, vec2(outTexCoord.x - uOffset.x, outTexCoord.y - uOffset.y));
  color *= 0.25;

  gl_FragColor = color;
}
`;

export default frag;
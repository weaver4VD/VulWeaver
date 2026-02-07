const frag = `\
#ifdef GL_FRAGMENT_PRECISION_HIGH
#define highmedp highp
#else
#define highmedp mediump
#endif
precision highmedp float;
uniform sampler2D uMainSampler; 
varying vec2 outTexCoord;
uniform float alpha;
uniform vec3 color;
uniform vec2 offset;

void main (void) {
  vec4 sample = texture2D(uMainSampler, outTexCoord - offset);
  sample.rgb = color.rgb * sample.a;
  sample *= alpha;

  gl_FragColor = sample;
}
`;

export default frag;
import { nodeResolve } from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import replace from '@rollup/plugin-replace';
import terser from '@rollup/plugin-terser';
import typescript from '@rollup/plugin-typescript';

export default {
    input: [
        './src/index.ts'
    ],
    output: {
        file: './dist/index.js',
        name: 'MyGame',
        format: 'iife',
        sourcemap: false
    },

    plugins: [
        replace({
            preventAssignment: true,
            'typeof CANVAS_RENDERER': JSON.stringify(true),
            'typeof WEBGL_RENDERER': JSON.stringify(true),
            'typeof WEBGL_DEBUG': JSON.stringify(false),
            'typeof EXPERIMENTAL': JSON.stringify(true),
            'typeof PLUGIN_CAMERA3D': JSON.stringify(false),
            'typeof PLUGIN_FBINSTANT': JSON.stringify(false),
            'typeof FEATURE_SOUND': JSON.stringify(true)
        }),
        nodeResolve({
            extensions: [ '.ts', '.tsx' ]
        }),
        commonjs({
            include: [
                'node_modules/eventemitter3/**',
                'node_modules/phaser/**'
            ],
            exclude: [ 
                'node_modules/phaser/src/polyfills/requestAnimationFrame.js',
                'node_modules/phaser/src/phaser-esm.js'
            ],
            sourceMap: false,
            ignoreGlobal: true
        }),
        typescript(),
        terser()

    ]
};
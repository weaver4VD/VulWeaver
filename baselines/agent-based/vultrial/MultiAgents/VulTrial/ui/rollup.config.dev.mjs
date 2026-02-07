import commonjs from '@rollup/plugin-commonjs';
import { nodeResolve } from '@rollup/plugin-node-resolve';
import replace from '@rollup/plugin-replace';
import serve from 'rollup-plugin-serve';
import typescript from '@rollup/plugin-typescript';


export default {
    input: [
        './src/index.ts'
    ],
    output: {
        file: './dist/bundle.js',
        name: 'MyGame',
        format: 'iife',
        sourcemap: true
    },

    plugins: [
        replace({
            preventAssignment: true,
            'typeof CANVAS_RENDERER': JSON.stringify(true),
            'typeof WEBGL_RENDERER': JSON.stringify(true),
            'typeof WEBGL_DEBUG': JSON.stringify(true),
            'typeof EXPERIMENTAL': JSON.stringify(true),
            'typeof PLUGIN_CAMERA3D': JSON.stringify(false),
            'typeof PLUGIN_FBINSTANT': JSON.stringify(false),
            'typeof FEATURE_SOUND': JSON.stringify(true)
        }),
        nodeResolve({
            browser: true,
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
            sourceMap: true,
            ignoreGlobal: true
        }),
        typescript(),
        serve({
            open: true,
            contentBase: 'dist',
            host: '127.0.0.1',
            port: 10001,
            headers: {
                'Access-Control-Allow-Origin': '*'
            }
        })

    ]
};

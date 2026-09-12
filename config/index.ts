import { defineConfig } from '@tarojs/cli'

export default defineConfig({
  projectName: 'zhiguan-miniapp',
  date: '2026-09-11',
  designWidth: 375,
  deviceRatio: {
    375: 2,
    640: 2.34,
    750: 2,
    828: 1.81,
  },
  sourceRoot: 'src',
  outputRoot: 'dist',
  framework: 'react',
  compiler: 'webpack5',
  babel: {
    presets: [['@babel/preset-typescript', { allExtensions: true, isTSX: true }]],
  },
  mini: {},
  h5: {},
})

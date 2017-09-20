const path = require('path')
const webpack = require('webpack')

const utils = require('./utils')

const projectRoot = path.resolve(__dirname, '../')
const isProduction = process.env.NODE_ENV === 'production'

module.exports = {
  entry: {
    app: ['babel-polyfill', './src/main.js']
  },
  output: {
    path: path.join(projectRoot, 'dist'),
    publicPath: '/',
    filename: 'build.js'
  },
  resolve: {
    extensions: ['.js', '.vue', '.css'],
    alias: {
      'src': path.join(projectRoot, 'src')
    }
  },
  module: {
    rules: [
      {
        test: /\.(js|vue)$/,
        loader: 'eslint-loader',
        enforce: 'pre',
        include: [path.join(projectRoot, 'src'), path.join(projectRoot, 'test')],
        options: {
          formatter: require('eslint-friendly-formatter')
        }
      },
      {
        test: /\.vue$/,
        use: [{
          loader: 'vue-loader',
          options: {
            preserveWhitespace: false,
            postcss: [
              require('postcss-cssnext')()
            ],
            loaders: utils.cssLoaders({
              minimize: isProduction,
              sourceMap: isProduction,
              extract: isProduction
            })
          }
        }]
      },
      {
        test: /\.js$/,
        loader: 'babel-loader',
        include: [
          path.join(projectRoot, 'src')
        ],
        exclude: /node_modules/
      },
      {
        test: /\.(png|jpg|gif|svg)$/,
        loader: 'file-loader',
        options: {
          name: '[name].[ext]?[hash]'
        }
      },
      {
        test: /\.(woff2?|eot|ttf|otf)$/,
        loader: 'file-loader',
        query: {
          name: 'font/[name].[hash:7].[ext]'
        }
      }
    ]
  },
  plugins: [
    new webpack.ProvidePlugin({
      // jquery
      $: 'jquery',
      jQuery: 'jquery',
      'window.jQuery': 'jquery'
    }),
    new webpack.NamedModulesPlugin()
  ],
  devServer: {
    historyApiFallback: true,
    noInfo: true,
    overlay: true
  },
  devtool: 'inline-source-map',
}

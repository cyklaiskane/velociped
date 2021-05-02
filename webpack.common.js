const path = require('path');
const webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');


module.exports = {
  entry: './src/index.js',
  plugins: [
    new webpack.ProgressPlugin(),
    new CleanWebpackPlugin(),
    new HtmlWebpackPlugin({
      title: 'Cykla i Skåne',
    }),
    new webpack.EnvironmentPlugin({
      API_BASE_URL: '',
    }),
    new webpack.IgnorePlugin({
      checkResource(resource) {
        return resource == 'osrm-text-instructions';
      }
    }),
  ],
  output: {
    filename: 'bundle.js',
    publicPath: '/assets/',
    path: path.resolve(__dirname, 'dist'),
  },
  module: {
    rules: [
      {
        test: /\.html$/i,
        loader: 'html-loader',
      },
      {
        test: /\.css$/,
        use: [
          'style-loader',
          'css-loader',
        ],
      },
      {
        test: /\.(png|svg|jpg|gif|eot|woff|woff2|ttf)$/,
        use: [
          'file-loader',
        ],
      },
    ],
  },
};
